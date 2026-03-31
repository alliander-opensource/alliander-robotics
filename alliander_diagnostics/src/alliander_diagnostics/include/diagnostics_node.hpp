// # SPDX-FileCopyrightText: Alliander N. V.
//
// # SPDX-License-Identifier: Apache-2.0

#ifndef DIAGNOSTICS_NODE_HPP_
#define DIAGNOSTICS_NODE_HPP_

#include <diagnostic_msgs/msg/diagnostic_array.hpp>
#include <rclcpp/rclcpp.hpp>

#include "base_diagnostics.hpp"

/**
 * @brief Node responsible for collecting and publishing diagnostics.
 *
 * This class manages a set of diagnostic modules derived from
 * BaseDiagnostics. It periodically evaluates each module and
 * publishes the combined diagnostic status as a DiagnosticArray.
 */
class DiagnosticsNode {
 public:
  /**
   * @brief Construct the diagnostics node.
   * @param node The ROS2 node.
   */
  DiagnosticsNode(rclcpp::Node::SharedPtr node);

 private:
  /// ROS2 node used for logging, parameters and communication.
  rclcpp::Node::SharedPtr node_;
  /// Publisher for the aggregated diagnostics message.
  rclcpp::Publisher<diagnostic_msgs::msg::DiagnosticArray>::SharedPtr pub_diag;
  /// Timer used to periodically trigger diagnostics evaluation.
  rclcpp::TimerBase::SharedPtr timer;
  /// Collection of diagnostic modules managed by this node.
  std::vector<std::shared_ptr<BaseDiagnostics>> diagnostics_modules;

  /**
   * @brief Timer callback that evaluates all diagnostic modules
   * and publishes the resulting diagnostic array.
   */
  void diagnostics_cb();
};

#endif  // DIAGNOSTICS_NODE_HPP_
