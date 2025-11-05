// # SPDX-FileCopyrightText: Alliander N. V.
//
// # SPDX-License-Identifier: Apache-2.0

#include <control_msgs/action/gripper_command.hpp>
#include <franka_msgs/action/grasp.hpp>
#include <franka_msgs/action/homing.hpp>
#include <franka_msgs/action/move.hpp>
#include <functional>
#include <rclcpp/client.hpp>
#include <rclcpp/executors.hpp>
#include <rclcpp/node.hpp>
#include <rclcpp/utilities.hpp>
#include <rclcpp_action/client.hpp>
#include <rclcpp_action/rclcpp_action.hpp>
#include <rclcpp_action/server.hpp>

using std::placeholders::_1;
using std::placeholders::_2;

typedef franka_msgs::action::Grasp Grasp;
typedef franka_msgs::action::Homing Homing;
typedef franka_msgs::action::Move Move;

typedef control_msgs::action::GripperCommand GripperCommand;

/** A node to simulate the fr3_gripper node of the real robot. */
class Fr3Gripper : public rclcpp::Node {
 public:
  Fr3Gripper();

 private:
  /** The lower limit of the gripper. */
  double lower_limit = 0.001;
  /** The upper limit of the gripper. */
  double upper_limit = 0.039;
  /** The acceptance tolerance when moving the gripper. */
  double tolerance = 0.001;

  /** The action client to control the gripper. */
  rclcpp_action::Client<GripperCommand>::SharedPtr client;

  /** The action server to accept grasp requests. */
  rclcpp_action::Server<Grasp>::SharedPtr grasp_server;
  /** The action server to accept homing requests. */
  rclcpp_action::Server<Homing>::SharedPtr homing_server;
  /** The action server to accept move requests. */
  rclcpp_action::Server<Move>::SharedPtr move_server;

  /**
   * @brief Handle goal requests
   *
   * @tparam action
   * @param uuid
   * @param goal
   * @return rclcpp_action::GoalResponse
   */
  template <typename action>
  rclcpp_action::GoalResponse handle_goal(
      const rclcpp_action::GoalUUID& uuid,
      std::shared_ptr<const typename action::Goal> goal);

  /**
   * @brief Handle cancel requests
   *
   * @tparam action
   * @param goal_handle
   * @return rclcpp_action::CancelResponse
   */
  template <typename action>
  rclcpp_action::CancelResponse handle_cancel(
      const std::shared_ptr<rclcpp_action::ServerGoalHandle<action>>
          goal_handle);

  /**
   * @brief Handle accepted goals
   *
   * @tparam action
   * @param goal_handle
   */
  template <typename action>
  void handle_accepted(
      const std::shared_ptr<rclcpp_action::ServerGoalHandle<action>>
          goal_handle);

  /**
   * @brief Template to execute an action
   *
   * @param goal_handle
   */
  template <typename action>
  void execute(const std::shared_ptr<rclcpp_action::ServerGoalHandle<action>>
                   goal_handle);

  /**
   * @brief Send a gripper command goal
   *
   * @param goal
   * @return bool
   */
  bool send_goal(const GripperCommand::Goal& goal);

  /**
   * @brief Check if the goal has been reached
   *
   * @param goal
   * @param result
   * @return bool
   */
  bool goal_reached(const GripperCommand::Goal& goal,
                    const GripperCommand::Result& result);

  /**
   * @brief Return the width respecting the limits
   *
   * @param width
   * @return double
   */
  double respect_limits(double width);
};
