// # SPDX-FileCopyrightText: Alliander N. V.
//
// # SPDX-License-Identifier: Apache-2.0

#ifndef IMU_BRIDGE_HPP_
#define IMU_BRIDGE_HPP_

#include <rclcpp/node.hpp>
#include <rclcpp/rclcpp.hpp>

#include "geometry_msgs/msg/vector3_stamped.hpp"
#include "sensor_msgs/msg/imu.hpp"

/// Class to publish Imu messages from acceleration/angular_velocity messages.
class ImuBridge : public rclcpp::Node {
 public:
  /**
   * @brief constructor for the ImuBridge class.
   * @param node The ROS2 node to attach to.
   */
  ImuBridge();
  ~ImuBridge() = default;

 private:
  // ROS2 communication variables:
  /// The ROS2 node
  rclcpp::Node::SharedPtr node;
  /// Subsciber for the acceleration topic
  rclcpp::Subscription<geometry_msgs::msg::Vector3Stamped>::SharedPtr sub_accel;
  /// Subscriber for the angular velocity topic
  rclcpp::Subscription<geometry_msgs::msg::Vector3Stamped>::SharedPtr
      sub_ang_vel;
  /// Publisher for the IMU topic
  rclcpp::Publisher<sensor_msgs::msg::Imu>::SharedPtr pub_imu;
  /// Timer for publishing IMU data
  rclcpp::TimerBase::SharedPtr timer_imu;

  /// Latest acceleration message
  geometry_msgs::msg::Vector3Stamped latest_accel_msg;
  /// Latest ang_vel message
  geometry_msgs::msg::Vector3Stamped latest_ang_vel_msg;

  /// Publish IMU message
  void publish_imu();
};

#endif  // IMU_BRIDGE_HPP_
