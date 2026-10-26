// # SPDX-FileCopyrightText: Alliander N. V.
//
// # SPDX-License-Identifier: Apache-2.0

#include <Eigen/Dense>
#include <gz/msgs.hh>
#include <gz/transport.hh>
#include <rclcpp/rclcpp.hpp>
#include <string>

/**
 * @brief A combined ROS2/Gazebo node to check the distance between the
 * transmitter of a charging station and the receiver of a robot. If the
 * distance is below a threshold, it toggles the charging state accordingly.
 */
class GZChargingChecker : public gz::transport::Node, public rclcpp::Node {
 public:
  GZChargingChecker() : rclcpp::Node("gz_charging_checker") {
    // Declare the required name parameters:
    for (const auto& [key, value] : names) {
      this->declare_parameter("name_" + key, "");
      this->get_parameter("name_" + key, names[key]);
      if (names[key].empty()) {
        RCLCPP_ERROR(this->get_logger(), "Parameter name_%s must be set",
                     key.c_str());
        return;
      }
    }

    // Declare optional parameters:
    this->declare_parameter("charging_distance_threshold", 0.05);
    this->get_parameter("charging_distance_threshold",
                        charging_distance_threshold_);

    // Create Gazebo subscriptions:
    std::array<std::string, 2> pose_topics = {
        "/model/" + names["robot"] + "/pose",
        "/model/" + names["station"] + "/pose"};
    for (auto topic : pose_topics) {
      if (!this->Subscribe(topic, &GZChargingChecker::callback, this)) {
        RCLCPP_ERROR(this->get_logger(), "Error subscribing to topic [%s]",
                     topic.c_str());
      }
    }
  }

 private:
  /// Map containing the names of the robot and the charging station.
  std::map<std::string, std::string> names{{"robot", ""}, {"station", ""}};

  /// Transformation matrix from the world frame to the robot frame.
  Eigen::Isometry3d transformation_world_robot_;
  /// Position vector of the robot's charging receiver in the robot frame.
  Eigen::Vector3d vector_robot_receiver_;
  /// Position vector of the robot's charging receiver in the world frame.
  Eigen::Vector3d vector_world_receiver_;

  /// Transformation matrix from the world frame to the charging station frame.
  Eigen::Isometry3d transformation_world_station_;
  /// Position vector of the charging transmitter in the station frame.
  Eigen::Vector3d vector_station_transmitter_;
  /// Position vector of the charging transmitter in the world frame.
  Eigen::Vector3d vector_world_transmitter_;

  /// Boolean indicating whether the robot is currently charging.
  bool is_charging_ = false;
  /// Distance between the receiver and transmitter.
  double distance_receiver_transmitter_;
  /// Threshold distance for initiating charging.
  double charging_distance_threshold_;

  /**
   * @brief The callback function for Gazebo poses message.
   *
   * @param msg The Gazebo pose message containing the poses..
   */
  void callback(const gz::msgs::Pose_V& msg) {
    for (const auto& pose : msg.pose()) {
      if (pose.name() == names["robot"]) {
        pose_to_transformation_matrix(pose, transformation_world_robot_);
      }
      if (pose.name().find("charging_receiver") != std::string::npos) {
        pose_to_position_vector(pose, vector_robot_receiver_);
      }

      if (pose.name() == names["station"]) {
        pose_to_transformation_matrix(pose, transformation_world_station_);
      }
      if (pose.name().find("charging_transmitter") != std::string::npos) {
        pose_to_position_vector(pose, vector_station_transmitter_);
      }
    }
    calculate_distance();
    toggle_charging();
  }

  /**
   * @brief Converts a Gazebo pose to a transformation matrix.
   *
   * @param pose The Gazebo pose message.
   * @param matrix The transformation matrix to be filled.
   */
  void pose_to_transformation_matrix(const gz::msgs::Pose& pose,
                                     Eigen::Isometry3d& matrix) {
    matrix.translation() << pose.position().x(), pose.position().y(),
        pose.position().z();
    Eigen::Quaterniond q(pose.orientation().w(), pose.orientation().x(),
                         pose.orientation().y(), pose.orientation().z());
    matrix.linear() = q.toRotationMatrix();
  }

  /**
   * @brief Converts a Gazebo pose to a position vector.
   *
   * @param pose The Gazebo pose message.
   * @param vector The position vector to be filled.
   */
  void pose_to_position_vector(const gz::msgs::Pose& pose,
                               Eigen::Vector3d& vector) {
    vector << pose.position().x(), pose.position().y(), pose.position().z();
  };

  /**
   * @brief Calculates the distance between the receiver and transmitter.
   */
  void calculate_distance() {
    vector_world_receiver_ =
        transformation_world_robot_ * vector_robot_receiver_;
    vector_world_transmitter_ =
        transformation_world_station_ * vector_station_transmitter_;
    distance_receiver_transmitter_ =
        (vector_world_receiver_ - vector_world_transmitter_).norm();
  }

  /**
   * @brief Toggles the charging state based on the distance between the
   * receiver and transmitter.
   */
  void toggle_charging() {
    gz::msgs::Boolean request;
    std::string action = "";
    if (distance_receiver_transmitter_ < charging_distance_threshold_) {
      action = "start";
    }
    if (distance_receiver_transmitter_ > charging_distance_threshold_) {
      action = "stop";
    }
    if (action == "start" && !is_charging_ ||
        action == "stop" && is_charging_) {
      std::string topic = "/model/" + names["robot"] + "/battery/" +
                          names["robot"] + "/battery/recharge/" + action;
      this->Request(topic, request);
      is_charging_ = !is_charging_;
      RCLCPP_INFO(this->get_logger(), "Charging %s.",
                  is_charging_ ? "started" : "stopped");
    }
  }
};

int main(int argc, char** argv) {
  rclcpp::init(argc, argv);
  GZChargingChecker gz_charging_checker;
  gz::transport::waitForShutdown();
  return 0;
}
