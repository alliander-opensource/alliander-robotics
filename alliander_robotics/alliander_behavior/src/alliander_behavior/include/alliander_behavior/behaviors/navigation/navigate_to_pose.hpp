// # SPDX-FileCopyrightText: Alliander N. V.
//
// # SPDX-License-Identifier: Apache-2.0
#pragma once

#include <behaviortree_ros2/bt_action_node.hpp>
#include <chrono>
#include <cstdint>
#include <geometry_msgs/msg/pose_stamped.hpp>
#include <mutex>
#include <nav2_msgs/action/navigate_to_pose.hpp>
#include <string>

namespace alliander_behavior {

/// Class that calls Nav2 behavior tree's NaviGateToPose action.
/// Causes the robot to navigate to a given waypoint in map frame.
class NavigateToPose
    : public BT::RosActionNode<nav2_msgs::action::NavigateToPose> {
 public:
  /**
   * @brief initializes the NavigateToPose object.
   * @param name the BT node name.
   * @param conf BT node config holding port mappings, runtime config, etc.
   * @param params ROS2 context for BT node.
   */
  NavigateToPose(const std::string& name, const BT::NodeConfig& conf,
                 const BT::RosNodeParams& params)
      : BT::RosActionNode<nav2_msgs::action::NavigateToPose>(name, conf,
                                                             params) {}

  /**
   * @brief fills out the BT.CPP ports.
   * @return BT.CPP ports list.
   */
  static BT::PortsList providedPorts() {
    return providedBasicPorts(
        {BT::InputPort<geometry_msgs::msg::PoseStamped>("pose",
                                                        "Pose to navigate to"),
         BT::OutputPort<uint16_t>("error_code",
                                  "Nav2 error code when navigation failed")});
  }

  /**
   * @brief overrides standard tick() behavior. Makes sure the node is spun
   * sufficiently to handle incoming action results.
   * @return status for this node.
   */
  BT::NodeStatus tick() override {
    // Jazzy's rclcpp_action only handles one item per exec spin.
    // behaviortree_ros2 only spins twice per BT tick.
    // Nav2 publishes feedback at a much higher rate than the tree ticks, so
    // the queue fills with feedback and the result is never handled.
    // Solution: drain the queue first, then tick.
    if (client_instance_ && status() == BT::NodeStatus::RUNNING) {
      std::unique_lock<std::mutex> lock(getMutex());
      client_instance_->callback_executor.spin_all(
          std::chrono::milliseconds(10));
    }
    return BT::RosActionNode<nav2_msgs::action::NavigateToPose>::tick();
  }

  /**
   * @brief overrides standard setGoal() behavior by checking ports and
   * logging.
   * @param goal BT.ROS2 Action Goal.
   * @return boolean indicating whether a goal was correctly constructed.
   */
  bool setGoal(Goal& goal) override {
    auto pose = getInput<geometry_msgs::msg::PoseStamped>("pose");
    if (!pose) {
      RCLCPP_ERROR(logger(), "%s: bad port [pose]: %s", name().c_str(),
                   pose.error().c_str());
      return false;
    }
    goal.pose = pose.value();
    return true;
  }

  /**
   * @brief callback triggered when a result is received. Logs an error, if
   * applicable.
   * @param wr Action Result wrapped in a BT.ROS2 object.
   * @return status for this BT node.
   */
  BT::NodeStatus onResultReceived(const WrappedResult& wr) override {
    if (wr.code == rclcpp_action::ResultCode::SUCCEEDED) {
      return BT::NodeStatus::SUCCESS;
    }
    const uint16_t error_code = wr.result ? wr.result->error_code : 0;
    RCLCPP_ERROR(logger(),
                 "%s: Nav2 failed with error code %u (action result code %d)",
                 name().c_str(), error_code, static_cast<int>(wr.code));
    setOutput("error_code", error_code);
    return BT::NodeStatus::FAILURE;
  }

  /**
   * @brief callback when the BT node produces a FAILURE state.
   * @param error the error to propagate to ROS logs.
   * @return status for this BT node.
   */
  BT::NodeStatus onFailure(BT::ActionNodeErrorCode error) override {
    RCLCPP_ERROR(logger(), "%s error: %s", name().c_str(), BT::toStr(error));
    return BT::NodeStatus::FAILURE;
  }

  /**
   * @brief overrides the default behavior when the tree is halted.
   */
  void onHalt() override {
    // goal cancels when halted anyway, this is just for logging.
    RCLCPP_INFO(logger(), "%s halted, cancelling the NavigateToPose goal",
                name().c_str());
  }
};

}  // namespace alliander_behavior
