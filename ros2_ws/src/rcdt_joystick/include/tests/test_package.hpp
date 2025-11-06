// # SPDX-FileCopyrightText: Alliander N. V.
//
// # SPDX-License-Identifier: Apache-2.0

#include <gtest/gtest.h>

#include <rcdt_joystick/joy_topic_manager.hpp>
#include <rclcpp/duration.hpp>
#include <rclcpp/executors.hpp>
#include <rclcpp/executors/multi_threaded_executor.hpp>
#include <rclcpp/executors/single_threaded_executor.hpp>
#include <rclcpp/future_return_code.hpp>
#include <rclcpp/rclcpp.hpp>
#include <sensor_msgs/msg/joy.hpp>

/**
 * Class to test the package.
 */
class PackageTester : public rclcpp::Node {
 public:
  PackageTester() : Node("joy_topic_manager_tester") {
    pub_joy_ = this->create_publisher<sensor_msgs::msg::Joy>("/joy", 1);
  }

  /**
   * @brief Publishes a Joy message with specified buttons/axes.
   * @param msg The sensor_msgs/Joy message to publish.
   */
  void publish_joy_message(const sensor_msgs::msg::Joy& msg) {
    pub_joy_->publish(msg);
  }

 private:
  /// Publisher for sensor_msgs/Joy messages.
  rclcpp::Publisher<sensor_msgs::msg::Joy>::SharedPtr pub_joy_;
};
