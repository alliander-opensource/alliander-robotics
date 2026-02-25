// # SPDX-FileCopyrightText: Alliander N. V.
//
// # SPDX-License-Identifier: Apache-2.0

#include "diagnostics.hpp"

Diagnostics::Diagnostics(rclcpp::Node::SharedPtr node) : node(node) {
  gps_topic = node->get_parameter("gps_topic").as_string();

  initialize_diagnostics();

  RCLCPP_INFO(node->get_logger(), "Diagnostics initialized.");
};

Diagnostics::~Diagnostics() {
  RCLCPP_INFO(node->get_logger(), "Shutdown complete.");
}

void Diagnostics::initialize_diagnostics() {
  // Subscibers
  sub_gps = node->create_subscription<sensor_msgs::msg::NavSatFix>(
      gps_topic, rclcpp::SensorDataQoS(),
      std::bind(&Diagnostics::gps_cb, this, _1));

  // Publishers
  pub_diagnostics =
      node->create_publisher<diagnostic_msgs::msg::DiagnosticArray>(
          "/system/diagnostics", 10);

  // Timer
  timer = node->create_timer(std::chrono::seconds(1),
                             std::bind(&Diagnostics::diagnostics_cb, this));
}

void Diagnostics::diagnostics_cb() {
  diagnostic_msgs::msg::DiagnosticArray diag_array;
  diag_array.header.stamp = node->now();

  {
    std::lock_guard<std::mutex> lock(diagnostics_mutex);

    // Push every stored sensor status
    diag_array.status.push_back(gps_status);
  }

  pub_diagnostics->publish(diag_array);
}

void Diagnostics::gps_cb(const sensor_msgs::msg::NavSatFix::SharedPtr msg) {
  std::lock_guard<std::mutex> lock(diagnostics_mutex);
  
  gps_status.name = "GPS Status";
  gps_status.hardware_id = "gps";  // We only accept a single GPS sensor
  gps_status.values.clear();

  if (!msg)
  {
    gps_status.level = diagnostic_msgs::msg::DiagnosticStatus::STALE;
    gps_status.message = "No GPS data received";
    return;
  }

  double covariance = msg->position_covariance[0];

  if (covariance > gps_covariance_limit) {
    if (!gps_high_covariance_detected) {
      gps_high_covariance_detected = true;
      gps_high_covariance_start_time = node->now();
    }
  } else {
    gps_high_covariance_detected = false;
  }

  if (msg->status.status < 0) {
    gps_status.level = diagnostic_msgs::msg::DiagnosticStatus::ERROR;
    gps_status.message = "GPS signal lost";
  } else if (gps_high_covariance_detected) {
    rclcpp::Duration duration = node->now() - gps_high_covariance_start_time;
    if (duration.seconds() < gps_signal_instability_limit) {
      gps_status.level = diagnostic_msgs::msg::DiagnosticStatus::WARN;
      gps_status.message = "GPS signal getting instable";
    } else {
      gps_status.level = diagnostic_msgs::msg::DiagnosticStatus::ERROR;
      gps_status.message = "GPS signal instable for too long";
    }
  } else {
    gps_status.level = diagnostic_msgs::msg::DiagnosticStatus::OK;
    gps_status.message = "GPS OK";
  }

  diagnostic_msgs::msg::KeyValue kv;
  kv.key = "GPS Position Covariance[0]";
  kv.value = std::to_string(msg->position_covariance[0]);
  gps_status.values.push_back(kv);
}
