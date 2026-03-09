// # SPDX-FileCopyrightText: Alliander N. V.
//
// # SPDX-License-Identifier: Apache-2.0

#include "diagnostics_node.hpp"

#include "gps_diagnostics.hpp"

DiagnosticsNode::DiagnosticsNode(rclcpp::Node::SharedPtr node) : node_(node) {
  // std::string gps_topic = node_->get_parameter("gps_topic").as_string();

  // diagnostics_modules.push_back(
  //     std::make_shared<GpsDiagnostics>(node_, gps_topic));

  pub_diag = node_->create_publisher<diagnostic_msgs::msg::DiagnosticArray>(
      "/system/diagnostics", 10);

  bool enable_gps = node_->get_parameter("enable_gps").as_bool();

  if (enable_gps) {
    std::string gps_topic = node_->get_parameter("gps_topic").as_string();

    diagnostics_modules.push_back(
        std::make_shared<GpsDiagnostics>(node_, gps_topic));

    RCLCPP_INFO(node_->get_logger(), "GPS diagnostics enabled");
  }

  timer = node_->create_wall_timer(
      std::chrono::seconds(1),
      std::bind(&DiagnosticsNode::diagnostics_cb, this));
}

void DiagnosticsNode::diagnostics_cb() {
  diagnostic_msgs::msg::DiagnosticArray array;

  array.header.stamp = node_->now();

  for (auto& module : diagnostics_modules) {
    module->evaluate(node_->now());

    array.status.push_back(module->get_status());
  }

  pub_diag->publish(array);
}
