// # SPDX-FileCopyrightText: Alliander N. V.
//
// # SPDX-License-Identifier: Apache-2.0

#include <cv_bridge/cv_bridge.hpp>
#include <opencv2/core/mat.hpp>
#include <opencv2/opencv.hpp>
#include <rclcpp/executors.hpp>
#include <rclcpp/node.hpp>
#include <rclcpp/publisher.hpp>
#include <rclcpp/subscription.hpp>
#include <sensor_msgs/msg/image.hpp>

using std::placeholders::_1;

typedef sensor_msgs::msg::Image Image;

/// Class to convert 32-bit float data to 16-bit unsigned int data.
class Convert32FC1to16UC1 : public rclcpp::Node {
 public:
  /// Constructor.
  Convert32FC1to16UC1();

 private:
  /// Subscription for 32-bit float data in m.
  rclcpp::Subscription<Image>::SharedPtr subscription;
  /// Publisher for 16-bit unsigned int data in mm.
  rclcpp::Publisher<Image>::SharedPtr publisher;
  /// Callback where data type and scale are changed.
  void subscription_callback(Image msg);
};
