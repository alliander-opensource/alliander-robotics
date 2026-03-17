// # SPDX-FileCopyrightText: Alliander N. V.
//
// # SPDX-License-Identifier: Apache-2.0

#include "gps_diagnostics.hpp"

#include <sys/resource.h>

#include <rclcpp/executors/multi_threaded_executor.hpp>
#include <rclcpp/node_options.hpp>

#include "diagnostics_node.hpp"

GpsDiagnostics::GpsDiagnostics(rclcpp::Node::SharedPtr node,
                               const std::string& topic)
    : BaseDiagnostics("GPS Status", "gps"), node_(node) {
  sub_gps = node_->create_subscription<sensor_msgs::msg::NavSatFix>(
      topic, rclcpp::SensorDataQoS(),
      std::bind(&GpsDiagnostics::gps_cb, this, std::placeholders::_1));
}

void GpsDiagnostics::gps_cb(const sensor_msgs::msg::NavSatFix::SharedPtr msg) {
  std::lock_guard<std::mutex> lock(mutex_);

  gps_msg_received = true;

  latest_msg_time = msg->header.stamp;
  latest_covariance =
      fmax(msg->position_covariance[0], msg->position_covariance[4]);
  latest_fix_status = msg->status.status;

  if (latest_covariance > gps_covariance_limit) {
    if (!high_covariance_detected) {
      high_covariance_detected = true;
      high_covariance_start_time = node_->now();
    }
  } else {
    high_covariance_detected = false;
  }
}

void GpsDiagnostics::evaluate(rclcpp::Time now) {
  std::lock_guard<std::mutex> lock(mutex_);

  status_.values.clear();

  if (!gps_msg_received) {
    // Never received GPS data
    status_.level = diagnostic_msgs::msg::DiagnosticStatus::STALE;
    status_.message = "No GPS data received";
    return;
  }

  rclcpp::Duration since_last = now - latest_msg_time;

  if (since_last > warning_timeout_) {
    // No data received in time
    status_.level = diagnostic_msgs::msg::DiagnosticStatus::WARN;
    status_.message = "Warning: no GPS signal received anymore";

    // Handle "no data received" escalations:
    if (since_last > stale_timeout_) {
      status_.level = diagnostic_msgs::msg::DiagnosticStatus::STALE;
      status_.message = "Stale: no GPS signal received";
    } else if (since_last > error_timeout_) {
      status_.level = diagnostic_msgs::msg::DiagnosticStatus::ERROR;
      status_.message = "Error: no GPS signal received";
    }

  } else if (latest_fix_status < 0) {
    // According to the GPS data, the signal is lost
    status_.level = diagnostic_msgs::msg::DiagnosticStatus::ERROR;
    status_.message = "GPS signal lost";
  } else if (high_covariance_detected) {
    rclcpp::Duration high_cov_duration = now - high_covariance_start_time;

    // Handle all "high covariance" escalations
    if (high_cov_duration > stale_timeout_) {
      status_.level = diagnostic_msgs::msg::DiagnosticStatus::STALE;
      status_.message = "Stale: high covariance for too long";
    } else if (high_cov_duration > error_timeout_) {
      status_.level = diagnostic_msgs::msg::DiagnosticStatus::ERROR;
      status_.message = "Error: high covariance for longer period";
    } else if (high_cov_duration > warning_timeout_) {
      status_.level = diagnostic_msgs::msg::DiagnosticStatus::WARN;
      status_.message = "Warning: high covariance";
    } else {
      status_.level = diagnostic_msgs::msg::DiagnosticStatus::OK;
      status_.message = "GPS OK, but high covariance noticed";
    }

  } else {
    // GPS data is OK
    status_.level = diagnostic_msgs::msg::DiagnosticStatus::OK;
    status_.message = "GPS OK";
  }

  diagnostic_msgs::msg::KeyValue kv;
  kv.key = "GPS Position Covariance";
  kv.value = std::to_string(latest_covariance);

  status_.values.push_back(kv);
}

int main(int argc, char** argv) {
  rclcpp::init(argc, argv);
  rclcpp::NodeOptions node_options;
  node_options.automatically_declare_parameters_from_overrides(true);
  rclcpp::Node::SharedPtr node =
      std::make_shared<rclcpp::Node>("alliander_diagnostics", node_options);
  DiagnosticsNode diagnostics(node);
  rclcpp::executors::MultiThreadedExecutor executor;
  executor.add_node(node);
  executor.spin();

  rclcpp::shutdown();
  return 0;
}
