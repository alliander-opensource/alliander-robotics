// # SPDX-FileCopyrightText: Alliander N. V.
//
// # SPDX-License-Identifier: Apache-2.0
#pragma once

#include <behaviortree_cpp/bt_factory.h>
#include <behaviortree_cpp/loggers/abstract_logger.h>

#include <rclcpp/logger.hpp>
#include <rclcpp/logging.hpp>

namespace alliander_behavior {

/// Class that allows BT.CPP messages to be published by a ROS node.
class RosStatusLogger : public BT::StatusChangeLogger {
 public:
  /**
   * @brief initializes the RosStatusLogger.
   * @param tree BTree instance to connect to.
   * @param logger the ROS2 logger instance to use for logging.
   */
  RosStatusLogger(const BT::Tree& tree, rclcpp::Logger logger)
      : BT::StatusChangeLogger(tree.rootNode()), logger_(std::move(logger)) {
    enableTransitionToIdle(false);
  }

  /**
   * @brief callback run every time a node from the BTree changes status.
   * @param node node of BTree that sends the message.
   * @param prev_status previos status of node.
   * @param status current status of node.
   */
  void callback(BT::Duration, const BT::TreeNode& node,
                BT::NodeStatus prev_status, BT::NodeStatus status) override {
    // only log to INFO if the Node is an Action Node. Otherwise, log to DEBUG
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

  /**
   * @brief ROS logging is handled immediately, there is no buffer.
   */
  void flush() override {}

 private:
  /// rclcpp Logger instance to log to.
  rclcpp::Logger logger_;
};

}  // namespace alliander_behavior
