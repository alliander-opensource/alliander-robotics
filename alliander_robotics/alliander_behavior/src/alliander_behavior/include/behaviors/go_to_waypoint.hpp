// # SPDX-FileCopyrightText: Alliander N. V.
//
// # SPDX-License-Identifier: Apache-2.0
#pragma once

#include <behaviortree_cpp/basic_types.h>

#include <behaviortree_ros2/bt_action_node.hpp>
#include <cmath>
#include <cstdint>
#include <nav2_msgs/action/navigate_to_pose.hpp>
#include <rclcpp_action/client.hpp>

#include "behaviortree_cpp/tree_node.h"
#include "geometry_msgs/msg/pose_stamped.hpp"

class GoToWaypoint
    : public BT::RosActionNode<nav2_msgs::action::NavigateToPose> {
 public:
  GoToWaypoint(const std::string& name, const BT::NodeConfig& conf,
               const BT::RosNodeParams& params)
      : BT::RosActionNode<nav2_msgs::action::NavigateToPose>(name, conf,
                                                             params) {}

  static BT::PortsList providedPorts() {
    return providedBasicPorts(
        {BT::InputPort<geometry_msgs::msg::PoseStamped>("pose",
                                                        "Pose to navigate to"),
         BT::OutputPort<uint16_t>("error_code",
                                  "Error produced by GoToWaypoint")});
  }

  BT::NodeStatus tick() override {
    // Jazzy's rclcpp_action only handles one item per exec spin.
    // behaviortree_ros2 only spins twice per BT tick (every 100 ms)
    // Nav2 publishes feedback at 100 Hz, while items are handled at 10 Hz.
    // So the queue is littered with feedback, which means the result is never
    // handled. Solution is to spin everything to clear the queue, then tick.
    if (client_instance_ && status() == BT::NodeStatus::RUNNING) {
      std::unique_lock<std::mutex> lock(getMutex());
      client_instance_->callback_executor.spin_all(
          std::chrono::milliseconds(10));
    }
    return BT::RosActionNode<nav2_msgs::action::NavigateToPose>::tick();
  }

  bool setGoal(Goal& goal) override {
    auto pose = getInput<geometry_msgs::msg::PoseStamped>("pose");
    if (!pose) {
      RCLCPP_ERROR(logger(), "GoToWaypoint: current_waypoint missing: %s",
                   pose.error().c_str());
      return false;
    }

    goal.pose = pose.value();
    return true;
  }

  BT::NodeStatus onResultReceived(const WrappedResult& wr) override {
    if (wr.code == rclcpp_action::ResultCode::SUCCEEDED) {
      return BT::NodeStatus::SUCCESS;
    }
    RCLCPP_ERROR(logger(),
                 "GoToWaypoint: Nav2 action failed with error code %d, causing "
                 "code %hhd in the BT.",
                 wr.result->error_code, static_cast<char>(wr.code));
    setOutput("error_code", wr.result->error_code);
    return BT::NodeStatus::FAILURE;
  }

  BT::NodeStatus onFailure(BT::ActionNodeErrorCode error) override {
    RCLCPP_ERROR(logger(), "GoToWaypoint error: %s", BT::toStr(error));
    return BT::NodeStatus::FAILURE;
  }

  void onHalt() override {
    RCLCPP_INFO(logger(),
                "GoToWaypoint halted. NavigateToPose goal is being cancelled");
  }
};
