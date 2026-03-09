// # SPDX-FileCopyrightText: Alliander N. V.
//
// # SPDX-License-Identifier: Apache-2.0

#ifndef GPS_DIAGNOSTICS_HPP_
#define GPS_DIAGNOSTICS_HPP_

#include <sensor_msgs/msg/nav_sat_fix.hpp>

#include "base_diagnostics.hpp"


/**
 * @brief Diagnostic module for monitoring GPS health.
 *
 * This class subscribes to a NavSatFix topic and evaluates the
 * quality and availability of the GPS signal. The diagnostic status
 * is updated based on message reception, covariance values, and
 * fix status.
 */
class GpsDiagnostics : public BaseDiagnostics {
 public:
  /**
   * @brief Construct a GPSDiagnostics instance.
   * @param node The ROS2 node to attach to.
   * @param topic The topic of the GPS to monitor.
   */
  GpsDiagnostics(rclcpp::Node::SharedPtr node, const std::string& topic);

 private:
  /// The ROS2 node
  rclcpp::Node::SharedPtr node_;

  /// Subsciber for the GPS topic
  rclcpp::Subscription<sensor_msgs::msg::NavSatFix>::SharedPtr sub_gps;

  /// Indication of whether a GPS message is received (true) or not (false)
  bool gps_msg_received = false;

  /// Header time in seconds from latest received GPS data
  rclcpp::Time latest_msg_time;
  /// Covariance value from latest received GPS data
  double latest_covariance = 0.0;
  /// Fix status from latest received GPS data
  int latest_fix_status = -1;

  /// The number of seconds of having received no data until the GPS signal is
  /// deemed to be unstable
  double no_data_received_limit = 5.0;

  /// Indication of whether a high covariance is detected (true) or not (false)
  bool high_covariance_detected = false;
  /// Start time of the detected high covariance value
  rclcpp::Time high_covariance_start_time;

  /// The limit of the GPS' covariance value, where a higher value indicates a
  /// weak signal
  double gps_covariance_limit = 30.0;
  /// The number of seconds of ERROR status until the GPS signal is officially
  /// deemed to be unstable
  double gps_signal_instability_limit = 5.0;

  /**
   * @brief Monitor the GPS topic and save the data received.
   * @param msg GPS fix message.
   */
  void gps_cb(const sensor_msgs::msg::NavSatFix::SharedPtr msg);

  /**
   * @brief Evaluate the monitored data and update the diagnostic status.
   * @param now current time.
   */
  void evaluate(rclcpp::Time now) override;

};

#endif  // GPS_DIAGNOSTICS_HPP_
