// # SPDX-FileCopyrightText: Alliander N. V.
//
// # SPDX-License-Identifier: Apache-2.0

#include "diagnostics_node.hpp"

#include "gps_diagnostics.hpp"

DiagnosticsNode::DiagnosticsNode(rclcpp::Node::SharedPtr node) : node_(node) {
  pub_diag = node_->create_publisher<diagnostic_msgs::msg::DiagnosticArray>(
      "/system/diagnostics", 10);

  std::vector<std::string> modules =
      node_->get_parameter("modules").as_string_array();

  for (const auto& module : modules) {
    if (module == "gps") {
      // make separate function of these contents (add_gps)
      GpsConfig config;

      config.fix_topic = node_->get_parameter("gps.topic").as_string();
      config.timeouts = node_->get_parameter("gps.timeouts").as_integer_array();

      diagnostics_modules.push_back(
          std::make_shared<GpsDiagnostics>(node_, config));

      RCLCPP_INFO(node_->get_logger(), "GPS diagnostics enabled");
    }
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
