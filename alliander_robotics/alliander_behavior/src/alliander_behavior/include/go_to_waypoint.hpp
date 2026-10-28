#pragma once

#include <behaviortree_cpp/basic_types.h>

#include <behaviortree_ros2/bt_action_node.hpp>
#include <cmath>
#include <nav2_msgs/action/navigate_to_pose.hpp>
#include <rclcpp_action/client.hpp>

#include "behaviortree_cpp/tree_node.h"

class GoToWaypoint
    : public BT::RosActionNode<nav2_msgs::action::NavigateToPose> {
 public:
  GoToWaypoint(const std::string& name, const BT::NodeConfig& conf,
               const BT::RosNodeParams& params)
      : BT::RosActionNode<nav2_msgs::action::NavigateToPose>(name, conf,
                                                             params) {}

  static BT::PortsList providedPorts() {
    return providedBasicPorts({BT::InputPort<std::string>(
        "action_name", "", "Action name to call action server for")});
  }

  bool setGoal(Goal& goal) override {
    // TriggerAction has no goal fields
    return true;
  }

  BT::NodeStatus onResultReceived(const WrappedResult& wr) override {
    if (wr.code == rclcpp_action::ResultCode::SUCCEEDED) {
      return BT::NodeStatus::SUCCESS;
    }
    setOutput("error_code", "Error from Nav2 behavior tree");
    return BT::NodeStatus::FAILURE;
  }

  BT::NodeStatus onFailure(BT::ActionNodeErrorCode error) override {
    RCLCPP_ERROR(logger(), "NavigateToPose error: %s", BT::toStr(error));
    return BT::NodeStatus::FAILURE;
  }

  void onHalt() override { RCLCPP_INFO(logger(), "NavigateToPose halted"); }
};
