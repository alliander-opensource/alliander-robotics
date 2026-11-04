// # SPDX-FileCopyrightText: Alliander N. V.
//
// # SPDX-License-Identifier: Apache-2.0
#pragma once

#include <behaviortree_cpp/bt_factory.h>
#include <behaviortree_cpp/loggers/abstract_logger.h>

#include <rclcpp/logger.hpp>
#include <rclcpp/logging.hpp>

class RosStatusLogger : public BT::StatusChangeLogger {
 public:
  RosStatusLogger(const BT::Tree& tree, rclcpp::Logger logger)
      : BT::StatusChangeLogger(tree.rootNode()), logger_(std::move(logger)) {
    enableTransitionToIdle(false);
  }

  void callback(BT::Duration, const BT::TreeNode& node,
                BT::NodeStatus prev_status, BT::NodeStatus status) override {
    const bool is_action = node.type() == BT::NodeType::ACTION;
    const bool verbose = is_action || status == BT::NodeStatus::SUCCESS;

    if (verbose) {
      RCLCPP_INFO(logger_, "%s: %s -> %s", node.fullPath().c_str(),
                  BT::toStr(prev_status, false).c_str(),
                  BT::toStr(status, false).c_str());
    } else {
      RCLCPP_DEBUG(logger_, "%s: %s -> %s", node.fullPath().c_str(),
                   BT::toStr(prev_status, false).c_str(),
                   BT::toStr(status, false).c_str());
    }
  }

  void flush() override {}

 private:
  rclcpp::Logger logger_;
};
