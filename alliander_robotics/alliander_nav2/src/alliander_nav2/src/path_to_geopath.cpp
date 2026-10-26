// # SPDX-FileCopyrightText: Alliander N. V.
//
// # SPDX-License-Identifier: Apache-2.0

#include <tf2_ros/buffer.h>
#include <tf2_ros/transform_listener.h>

#include <GeographicLib/UTMUPS.hpp>
#include <alliander_interfaces/msg/utm_datum.hpp>
#include <geographic_msgs/msg/geo_path.hpp>
#include <geometry_msgs/msg/pose_stamped.hpp>
#include <nav_msgs/msg/path.hpp>
#include <rclcpp/rclcpp.hpp>
#include <tf2_geometry_msgs/tf2_geometry_msgs.hpp>

using alliander_interfaces::msg::UTMDatum;
using geographic_msgs::msg::GeoPath;
using geographic_msgs::msg::GeoPoseStamped;
using geometry_msgs::msg::PoseStamped;
using geometry_msgs::msg::TransformStamped;
using nav_msgs::msg::Path;
using std::placeholders::_1;

/**
 * @brief A ROS2 node that converts a Path to a GeoPath.
 */
class RouteToGps : public rclcpp::Node {
 public:
  RouteToGps()
      : Node("route_to_gps"),
        tf_buffer_(get_clock()),
        tf_listener_(tf_buffer_) {
    rclcpp::QoS qos(1);
    qos.transient_local();
    utm_sub_ = create_subscription<UTMDatum>(
        "/utm_datum", qos, std::bind(&RouteToGps::utmCallback, this, _1));

    plan_pub_ = create_publisher<GeoPath>("/plan_gps", 10);
    plan_sub_ = create_subscription<Path>(
        "/plan", 10, std::bind(&RouteToGps::planCallback, this, _1));
  }

 private:
  /// TF2 buffer
  tf2_ros::Buffer tf_buffer_;
  /// TF2 transform listener
  tf2_ros::TransformListener tf_listener_;

  /// Publisher for the navigation plan in lat long coordinates
  rclcpp::Publisher<GeoPath>::SharedPtr plan_pub_;

  /// Subscriber that listens to the UTM configuration
  rclcpp::Subscription<UTMDatum>::SharedPtr utm_sub_;
  /// Subscriber that listens to the navigation plan
  rclcpp::Subscription<Path>::SharedPtr plan_sub_;

  /// UTM Datum:
  UTMDatum utm_datum_;

  /**
   * @brief Callback function for the UTM datum.
   *
   * @param msg The UTM datum message.
   */
  void utmCallback(const UTMDatum::SharedPtr msg) { utm_datum_ = *msg; }

  /**
   * @brief Callback function for the navigation plan.
   *
   * Converts the plan from the "map" frame to GPS coordinates and publishes it.
   *
   * @param msg The navigation plan in the "map" frame.
   */
  void planCallback(const Path::SharedPtr msg) {
    // Check if a valid UTM datum has been set:
    if (utm_datum_.zone < 0 || utm_datum_.zone > 60) {
      RCLCPP_WARN(get_logger(),
                  "No valid UTM zone set. Cannot convert plan to GPS.");
      return;
    }

    // Get the transform from the map frame to the UTM frame:
    TransformStamped map_to_utm;
    try {
      map_to_utm = tf_buffer_.lookupTransform("utm", "map", tf2::TimePointZero);
    } catch (const tf2::TransformException& ex) {
      RCLCPP_WARN(get_logger(), "Could not transform map to utm: %s",
                  ex.what());
      return;
    }

    // Transform poses from map to latlong:
    GeoPath gps_path;
    gps_path.header = msg->header;
    gps_path.poses.reserve(msg->poses.size());

    try {
      for (const auto& pose : msg->poses) {
        PoseStamped utm_pose;
        GeoPoseStamped gps_pose;

        tf2::doTransform(pose, utm_pose, map_to_utm);
        GeographicLib::UTMUPS::Reverse(
            utm_datum_.zone, utm_datum_.northp, utm_pose.pose.position.x,
            utm_pose.pose.position.y, gps_pose.pose.position.latitude,
            gps_pose.pose.position.longitude);

        gps_pose.header = pose.header;
        gps_pose.pose.position.altitude = utm_pose.pose.position.z;
        gps_path.poses.push_back(std::move(gps_pose));
      }
    } catch (const std::exception& ex) {
      RCLCPP_WARN(get_logger(), "Could not convert plan to GPS coordinates: %s",
                  ex.what());
      return;
    }

    plan_pub_->publish(gps_path);
  }
};

int main(int argc, char* argv[]) {
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<RouteToGps>());
  rclcpp::shutdown();
  return 0;
}
