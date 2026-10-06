// # SPDX-FileCopyrightText: Alliander N. V.
//
// # SPDX-License-Identifier: Apache-2.0

#include <tf2_ros/buffer.h>
#include <tf2_ros/transform_listener.h>

#include <GeographicLib/GeoCoords.hpp>
#include <geographic_msgs/msg/geo_path.hpp>
#include <memory>
#include <nav_msgs/msg/path.hpp>
#include <rclcpp/rclcpp.hpp>
#include <robot_localization/srv/set_datum.hpp>
#include <sensor_msgs/msg/nav_sat_fix.hpp>
#include <sensor_msgs/msg/nav_sat_status.hpp>
#include <std_srvs/srv/empty.hpp>
#include <tf2_geometry_msgs/tf2_geometry_msgs.hpp>

using geographic_msgs::msg::GeoPath;
using geographic_msgs::msg::GeoPoseStamped;
using geometry_msgs::msg::PoseStamped;
using geometry_msgs::msg::TransformStamped;
using nav_msgs::msg::Path;
using robot_localization::srv::SetDatum;
using sensor_msgs::msg::NavSatFix;
using sensor_msgs::msg::NavSatStatus;
using std::placeholders::_1;
using std_srvs::srv::Empty;
using namespace std::chrono_literals;

/**
 * @brief A ROS2 node that gates the robot_localization datum on a run of
 * consecutive, sufficiently-precise GPS fixes.
 *
 * Listens on the gps/fix topic and, once required_consecutive_fixes_ good
 * fixes in a row have been seen, calls robot_localization's datum service
 * with that fix.
 *
 * The corresponding UTM zone and hemisphere are stored and used by the node to
 * convert map coordinates to GPS coordinates.
 */
class GeoreferencingNode : public rclcpp::Node {
 public:
  /**
   * @brief Constructor for the OdometryGateNode class.
   */
  GeoreferencingNode()
      : Node("initialize_odom_node"),
        tf_buffer_(get_clock()),
        tf_listener_(tf_buffer_) {
    std::string ns = this->get_namespace();
    plan_pub_ = create_publisher<GeoPath>(ns + "/plan_gps", 10);
    datum_client_ = create_client<SetDatum>("datum");
    odometry_toggle_client_ = create_client<Empty>("enable");
    required_consecutive_fixes_ =
        declare_parameter<int>("required_consecutive_fixes", 5);
    max_position_covariance_ =
        declare_parameter<double>("max_position_covariance_m2", 4.0);
    plan_sub_ = create_subscription<Path>(
        ns + "/plan", 10,
        std::bind(&GeoreferencingNode::planCallback, this, _1));
    fix_sub_ = create_subscription<NavSatFix>(
        "gps/fix", 10, std::bind(&GeoreferencingNode::fixCallback, this, _1));

    RCLCPP_INFO(get_logger(),
                "Waiting for %d consecutive good fixes on before setting datum "
                "and enabling global EKF",
                required_consecutive_fixes_);
  }

 private:
  /**
   * @brief Callback for the GPS fix subscription.
   *
   * Tracks the streak of consecutive good fixes, resetting it whenever a
   * fix falls out of tolerance, and triggers setDatum() once the streak
   * reaches required_consecutive_fixes_.
   * @param msg Shared pointer to the incoming NavSatFix message.
   */
  void fixCallback(const NavSatFix::SharedPtr msg) {
    if (odometry_enabled_) {
      return;
    }

    if (!isGoodFix(*msg)) {
      if (consecutive_good_fixes_ > 0) {
        RCLCPP_WARN(get_logger(),
                    "Fix dropped out of tolerance, resetting streak");
      }
      consecutive_good_fixes_ = 0;
      RCLCPP_WARN_THROTTLE(
          get_logger(), *get_clock(), 5000,
          "Fix not good enough yet (status=%d, covariance=%.7f,%.7f)",
          msg->status.status, msg->position_covariance[0],
          msg->position_covariance[4]);
      return;
    }

    ++consecutive_good_fixes_;
    RCLCPP_INFO(
        get_logger(),
        "Good fix %d/%d (lat=%.7f, lon=%.7f, status=%d, covariance=%.7f,%.7f)",
        consecutive_good_fixes_, required_consecutive_fixes_, msg->latitude,
        msg->longitude, msg->status.status, msg->position_covariance[0],
        msg->position_covariance[4]);

    if (consecutive_good_fixes_ < required_consecutive_fixes_) {
      return;
    }

    setDatum(*msg);
    enableOdometry();
  }

  /**
   * @brief Checks whether a fix meets the status and covariance
   * requirements to count toward the good-fix streak.
   *
   * @param msg NavSatFix message to evaluate.
   * @return bool True if the fix has at least STATUS_FIX, a known
   * covariance type, and horizontal covariance within
   * max_position_covariance_.
   */
  bool isGoodFix(const NavSatFix& msg) const {
    // Require a fix
    if (msg.status.status < NavSatStatus::STATUS_FIX) {
      return false;
    }

    // Require a covariance
    if (msg.position_covariance_type == NavSatFix::COVARIANCE_TYPE_UNKNOWN) {
      return false;
    }

    // Covariance check
    double horizontal_cov =
        std::max(msg.position_covariance[0], msg.position_covariance[4]);
    if (horizontal_cov <= 0.0 || horizontal_cov > max_position_covariance_) {
      return false;
    }

    // TODO add RTK-fix condition?
    return true;
  }

  /**
   * @brief Sends the SetDatum request for the given fix.
   *
   * @param msg The qualifying NavSatFix to use as the datum.
   */
  void setDatum(const NavSatFix& msg) {
    if (!datum_client_->wait_for_service(1s)) {
      RCLCPP_WARN(get_logger(),
                  "datum service not up yet, will retry on next good fix");
      consecutive_good_fixes_ = 0;
      return;
    }

    GeographicLib::GeoCoords gc(msg.latitude, msg.longitude);
    utm_zone_ = gc.Zone();
    utm_north_ = (gc.Hemisphere() == 'n');

    auto request = std::make_shared<SetDatum::Request>();
    request->geo_pose.position.latitude = msg.latitude;
    request->geo_pose.position.longitude = msg.longitude;
    request->geo_pose.position.altitude = msg.altitude;
    request->geo_pose.orientation.w = 1.0;

    datum_client_->async_send_request(
        request, [this](rclcpp::Client<SetDatum>::SharedFuture) {
          RCLCPP_INFO(get_logger(), "Datum set");
        });
  }

  /**
   * @brief Sends an Empty service request to the enable service for the global
   * EKF
   */
  void enableOdometry() {
    if (!odometry_toggle_client_->wait_for_service(1s)) {
      RCLCPP_WARN(
          get_logger(),
          "odometry toggle service not up yet, will retry on next good fix");
      consecutive_good_fixes_ = 0;
      return;
    }

    auto request = std::make_shared<Empty::Request>();
    odometry_enabled_ = true;
    odometry_toggle_client_->async_send_request(
        request, [this](rclcpp::Client<Empty>::SharedFuture) {
          RCLCPP_INFO(get_logger(), "Global EKF enabled");
        });
  }

  /**
   * @brief Callback function for the navigation plan.
   *
   * Converts the plan from the "map" frame to GPS coordinates and publishes it.
   *
   * @param msg The navigation plan in the "map" frame.
   */
  void planCallback(const Path::SharedPtr msg) {
    TransformStamped map_to_utm;
    try {
      map_to_utm = tf_buffer_.lookupTransform("utm", "map", tf2::TimePointZero);
    } catch (const tf2::TransformException& ex) {
      RCLCPP_WARN(get_logger(), "Could not transform map to utm: %s",
                  ex.what());
      return;
    }

    GeoPath gps_path;
    gps_path.header = msg->header;
    gps_path.header.frame_id = "wgs84";
    gps_path.poses.reserve(msg->poses.size());

    try {
      for (const auto& pose : msg->poses) {
        PoseStamped utm_pose;
        tf2::doTransform(pose, utm_pose, map_to_utm);

        GeographicLib::GeoCoords gc(utm_zone_, utm_north_,
                                    utm_pose.pose.position.x,
                                    utm_pose.pose.position.y);

        GeoPoseStamped gps_pose;
        gps_pose.header = utm_pose.header;
        gps_pose.header.frame_id = "wgs84";
        gps_pose.pose.position.latitude = gc.Latitude();
        gps_pose.pose.position.longitude = gc.Longitude();
        gps_pose.pose.position.altitude = utm_pose.pose.position.z;
        gps_pose.pose.orientation = utm_pose.pose.orientation;
        gps_path.poses.push_back(std::move(gps_pose));
      }
    } catch (const std::exception& ex) {
      RCLCPP_WARN(get_logger(), "Could not convert plan to GPS coordinates: %s",
                  ex.what());
      return;
    }

    plan_pub_->publish(gps_path);
  }

  /// TF2 buffer
  tf2_ros::Buffer tf_buffer_;
  /// TF2 transform listener
  tf2_ros::TransformListener tf_listener_;

  /// Publisher for the navigation plan in lat long coordinates
  rclcpp::Publisher<GeoPath>::SharedPtr plan_pub_;

  /// Subscriber that listens to the GPS fix topic
  rclcpp::Subscription<sensor_msgs::msg::NavSatFix>::SharedPtr fix_sub_;
  /// Subscriber that listens to the navigation plan
  rclcpp::Subscription<Path>::SharedPtr plan_sub_;

  /// Client to robot_localization's set_datum service
  rclcpp::Client<SetDatum>::SharedPtr datum_client_;
  /// Client to enable global EKF
  rclcpp::Client<Empty>::SharedPtr odometry_toggle_client_;

  /// Number of consecutive good fixes required before setting the datum
  int required_consecutive_fixes_;
  /// Maximum acceptable horizontal position covariance, in m^2
  double max_position_covariance_;
  /// Current length of the consecutive good-fix streak
  int consecutive_good_fixes_ = 0;
  /// Whether odometry is already enabled (gate satisfied)
  bool odometry_enabled_ = false;
  /// UTM zone
  int utm_zone_;
  /// Whether the UTM zone is in the northern hemisphere
  bool utm_north_;
};

int main(int argc, char** argv) {
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<GeoreferencingNode>());
  rclcpp::shutdown();
  return 0;
}
