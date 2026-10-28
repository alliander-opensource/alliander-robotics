#pragma once

#include <behaviortree_cpp/basic_types.h>

#include <alliander_interfaces/action/trigger_action.hpp>
#include <behaviortree_ros2/bt_action_node.hpp>
#include <cmath>
#include <rclcpp_action/client.hpp>

#include "alliander_interfaces/action/trigger_action.hpp"
#include "behaviortree_cpp/tree_node.h"

class CallTriggerAction
    : public BT::RosActionNode<alliander_interfaces::action::TriggerAction> {
 public:
  CallTriggerAction(const std::string& name, const BT::NodeConfig& conf,
                    const BT::RosNodeParams& params)
      : BT::RosActionNode<alliander_interfaces::action::TriggerAction>(
            name, conf, params) {}

  static BT::PortsList providedPorts() {
    return providedBasicPorts({BT::InputPort<std::string>(
        "action_name", "", "Action name to call action server for")});
  }

  bool setGoal(Goal& goal) override {
    // TriggerAction has no goal fields
    return true;
  }

  BT::NodeStatus onResultReceived(const WrappedResult& wr) override {
    if (wr.code == rclcpp_action::ResultCode::SUCCEEDED && wr.result->success) {
      return BT::NodeStatus::SUCCESS;
    }
    setOutput("error_code", wr.result ? wr.result->message : "Unknown error");
    return BT::NodeStatus::FAILURE;
  }

  BT::NodeStatus onFailure(BT::ActionNodeErrorCode error) override {
    RCLCPP_ERROR(logger(), "TriggerAction error: %s", BT::toStr(error));
    return BT::NodeStatus::FAILURE;
  }

  BT::NodeStatus onFeedback(
      const std::shared_ptr<const Feedback> feedback) override {
    RCLCPP_DEBUG(logger(), "TriggerAction feedback: %s",
                 feedback->status.c_str());
    return BT::NodeStatus::RUNNING;
  }

  void onHalt() override { RCLCPP_INFO(logger(), "TriggerAction halted"); }
};
