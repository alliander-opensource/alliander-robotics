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
  latest_covariance = msg->position_covariance[0];
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
    status_.level = diagnostic_msgs::msg::DiagnosticStatus::STALE;
    status_.message = "No GPS data received";
    return;
  }

  rclcpp::Duration since_last = now - latest_msg_time;

  if (since_last.seconds() > limit_no_data_received) {
    status_.level = diagnostic_msgs::msg::DiagnosticStatus::ERROR;
    status_.message = "No GPS signal received anymore";
  } else if (latest_fix_status < 0) {
    status_.level = diagnostic_msgs::msg::DiagnosticStatus::ERROR;
    status_.message = "GPS signal lost";
  } else if (high_covariance_detected) {
    rclcpp::Duration duration = now - high_covariance_start_time;

    if (duration.seconds() < gps_signal_instability_limit) {
      status_.level = diagnostic_msgs::msg::DiagnosticStatus::WARN;
      status_.message = "GPS signal getting instable";
    } else {
      status_.level = diagnostic_msgs::msg::DiagnosticStatus::ERROR;
      status_.message = "GPS signal instable for too long";
    }
  } else {
    status_.level = diagnostic_msgs::msg::DiagnosticStatus::OK;
    status_.message = "GPS OK";
  }

  diagnostic_msgs::msg::KeyValue kv;
  kv.key = "GPS Position Covariance[0]";
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
