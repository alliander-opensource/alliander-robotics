// # SPDX-FileCopyrightText: Alliander N. V.
//
// # SPDX-License-Identifier: Apache-2.0

#include <cstdint>
#include <string>
#include <thread>

#include "behaviortree_cpp/bt_factory.h"
#include "behaviortree_cpp/condition_node.h"
#include "diagnostic_msgs/msg/diagnostic_array.hpp"
#include "rclcpp/rclcpp.hpp"

namespace nav2_behavior_tree {

/**
 * @brief A Behavior Tree condition node that checks the health of the GPS
 * sensor.
 */
class IsSystemHealthy : public BT::ConditionNode {
 public:
  /**
   * @brief constructor for the IsSystemHealthy class.
   *
   * @param name Name of the BT node.
   * @param config Node configuration including blackboard.
   */
  IsSystemHealthy(const std::string& name, const BT::NodeConfiguration& config)
      : BT::ConditionNode(name, config),
        gps_status_(diagnostic_msgs::msg::DiagnosticStatus::OK) {
    // Get the shared Nav2 node from blackboard
    node_ = config.blackboard->get<rclcpp::Node::SharedPtr>("node");

    // Create a dedicated callback group
    callback_group_ = node_->create_callback_group(
        rclcpp::CallbackGroupType::MutuallyExclusive, false);

    // Spin the callback group in a separate executor thread
    callback_group_executor_.add_callback_group(
        callback_group_, node_->get_node_base_interface());
    callback_group_executor_thread_ =
        std::thread([this]() { callback_group_executor_.spin(); });

    // Subscription options to attach to callback group
    rclcpp::SubscriptionOptions sub_options;
    sub_options.callback_group = callback_group_;

    sub_ = node_->create_subscription<diagnostic_msgs::msg::DiagnosticArray>(
        "/system/diagnostics", 10,
        std::bind(&IsSystemHealthy::callback, this, std::placeholders::_1),
        sub_options);

    RCLCPP_INFO(node_->get_logger(), "Initialized IsSystemHealthy BT node");
  }

  /**
   * @brief Destructor of the IsSystemHealthy class.
   */
  ~IsSystemHealthy() {
    RCLCPP_INFO(node_->get_logger(), "Shutting down IsSystemHealthy BT node");

    // Stop the executor and join the thread
    callback_group_executor_.cancel();
    if (callback_group_executor_thread_.joinable()) {
      callback_group_executor_thread_.join();
    }
  }

  /**
   * @brief Provides the list of ports for this BT node.
   *
   * @return BT::PortsList Empty list (no ports for this node)
   */
  static BT::PortsList providedPorts() { return {}; }

  /**
   * @brief Tick function for the BT node to check the GPS status and respond
   * accordingly. For any status worse than a warning, the GPS health condition
   * should fail.
   *
   * @return BT::NodeStatus Node execution status.
   */
  BT::NodeStatus tick() override {
    if (gps_status_ > diagnostic_msgs::msg::DiagnosticStatus::WARN) {
      RCLCPP_WARN_THROTTLE(node_->get_logger(), *node_->get_clock(), 5000,
                           "GPS unhealthy (code %u), pausing FollowPath",
                           gps_status_);
      return BT::NodeStatus::RUNNING;  // Keep tree RUNNING until GPS recovers
    }
    return BT::NodeStatus::SUCCESS;
  }

 private:
  /**
   * @brief Callback for the diagnostics topic.
   *
   * @param msg Shared pointer to a DiagnosticArray message.
   */
  void callback(const diagnostic_msgs::msg::DiagnosticArray::SharedPtr msg) {
    for (const auto& status : msg->status) {
      if (status.hardware_id == "gps") {
        gps_status_ = status.level;
        RCLCPP_DEBUG(node_->get_logger(), "GPS status updated: %u",
                     gps_status_);
      }
    }
  }

  /// The ROS2 node
  rclcpp::Node::SharedPtr node_;
  /// Callback group for the GPS subscription
  rclcpp::CallbackGroup::SharedPtr callback_group_;
  /// Single-threaded executor for the callback group
  rclcpp::executors::SingleThreadedExecutor callback_group_executor_;
  /// Thread that runs the callback group executor
  std::thread callback_group_executor_thread_;
  /// Subscriber that listens to the diagnostics topic
  rclcpp::Subscription<diagnostic_msgs::msg::DiagnosticArray>::SharedPtr sub_;
  /// Status of the GPS sensor
  uint8_t gps_status_;
};

}  // namespace nav2_behavior_tree

// Register the BT node
#include "behaviortree_cpp/bt_factory.h"

BT_REGISTER_NODES(factory) {
  factory.registerNodeType<nav2_behavior_tree::IsSystemHealthy>(
      "IsSystemHealthy");
}
