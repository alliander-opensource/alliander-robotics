// # SPDX-FileCopyrightText: Alliander N. V.
//
// # SPDX-License-Identifier: Apache-2.0

#ifndef DIAGNOSTICS_HPP_
#define DIAGNOSTICS_HPP_

#include <diagnostic_msgs/msg/diagnostic_array.hpp>
#include <mutex>
#include <rclcpp/node.hpp>
#include <rclcpp/node_options.hpp>
#include <rclcpp/rclcpp.hpp>
#include <sensor_msgs/msg/nav_sat_fix.hpp>
#include <string>

using std::placeholders::_1;
using std::placeholders::_2;

/// Class to monitor system diagnostics.
class Diagnostics {
 public:
  /**
   * @brief constructor for the Diagnostics class.
   * @param node The ROS2 node to attach to.
   */
  Diagnostics(rclcpp::Node::SharedPtr node);
  ~Diagnostics();

 private:
  // ROS2 communication variables:
  /// The ROS2 node
  rclcpp::Node::SharedPtr node;
  /// Subsciber for the GPS topic
  rclcpp::Subscription<sensor_msgs::msg::NavSatFix>::SharedPtr sub_gps;
  /// Publisher for the diagnostic data
  rclcpp::Publisher<diagnostic_msgs::msg::DiagnosticArray>::SharedPtr
      pub_diagnostics;
  /// Timer that triggers the diagnostics callback to send the data at a
  /// constant rate
  rclcpp::TimerBase::SharedPtr timer;

  // ROS2 get parameter variables:
  /// The GPS data topic
  std::string gps_topic;
  /// The GPS status
  diagnostic_msgs::msg::DiagnosticStatus gps_status{};
  /// The GPS status
  bool gps_high_covariance_detected;
  /// The GPS status
  rclcpp::Time gps_high_covariance_start_time;
  /// The limit of the GPS' covariance value, where a higher value indicates a
  /// weak signal
  double gps_covariance_limit{100.0};
  /// The number of seconds of ERROR status until the GPS signal is officially
  /// deemed to be unstable
  double gps_signal_instability_limit{10.0};

  // Other variables
  /// Mutex to protect shared data
  std::mutex diagnostics_mutex;

  /**
   * @brief initialize the diagnostics node.
   */
  void initialize_diagnostics();

  /**
   * @brief callback method that publishes all diagnostic data at a constant
   * rate.
   */
  void diagnostics_cb();

  /**
   * @brief callback method that handles the data received from the GPS sensor.
   * @param msg gps message.
   */
  void gps_cb(const sensor_msgs::msg::NavSatFix::SharedPtr msg);
};

#endif  // DIAGNOSTICS_HPP_
