// # SPDX-FileCopyrightText: Alliander N. V.
//
// # SPDX-License-Identifier: Apache-2.0
#pragma once

#include <alliander_interfaces/action/trigger_action.hpp>
#include <behaviortree_ros2/bt_action_node.hpp>
#include <string>

namespace alliander_behavior {

/// Generic class that calls a TriggerAction and handles the result.
class CallTriggerAction
    : public BT::RosActionNode<alliander_interfaces::action::TriggerAction> {
 public:
  /**
   * @brief initializes a CallTriggerAction object.
   * @param name BT node name.
   * @param conf BT node config, including port mappings.
   * @param params ROS2 context.
   */
  CallTriggerAction(const std::string& name, const BT::NodeConfig& conf,
                    const BT::RosNodeParams& params)
      : BT::RosActionNode<alliander_interfaces::action::TriggerAction>(
            name, conf, params) {}

  /**
   * @brief fills out BT.CPP's ports list.
   * @return BT ports list.
   */
  static BT::PortsList providedPorts() {
    return providedBasicPorts({BT::OutputPort<std::string>(
        "error_message", "Reason the action failed")});
  }

  /**
   * @brief overrides default setGoal() behavior.
   * @return true since the goal part of the message is empty.
   */
  bool setGoal(Goal&) override { return true; }

  /**
   * @brief callback when an action result is received.
   * @param wr wrapped BT.ROS2 Result type.
   * @return status of this node, indicating whether the action succeeded.
   */
  BT::NodeStatus onResultReceived(const WrappedResult& wr) override {
    if (wr.code == rclcpp_action::ResultCode::SUCCEEDED && wr.result &&
        wr.result->success) {
      return BT::NodeStatus::SUCCESS;
    }
    const std::string message =
        wr.result ? wr.result->message : "action returned no result";
    RCLCPP_WARN(logger(), "%s failed: %s", name().c_str(), message.c_str());
    setOutput("error_message", message);
    return BT::NodeStatus::FAILURE;
  }

  /**
   * @brief callback when the action failed.
   * @param error error to propagate to ROS2 logs.
   * @return status of this node.
   */
  BT::NodeStatus onFailure(BT::ActionNodeErrorCode error) override {
    RCLCPP_ERROR(logger(), "%s error: %s", name().c_str(), BT::toStr(error));
    setOutput("error_message", std::string(BT::toStr(error)));
    return BT::NodeStatus::FAILURE;
  }

  /**
   * @brief callback when Action Feedback is received.
   * @param feedback generic BT.ROS2 feedback message.
   * @return status of this node.
   */
  BT::NodeStatus onFeedback(
      const std::shared_ptr<const Feedback> feedback) override {
    RCLCPP_DEBUG(logger(), "%s feedback: %s", name().c_str(),
                 feedback->status.c_str());
    return BT::NodeStatus::RUNNING;
  }

  /**
   * @brief callback when node is halted.
   */
  void onHalt() override { RCLCPP_INFO(logger(), "%s halted", name().c_str()); }
};

}  // namespace alliander_behavior
