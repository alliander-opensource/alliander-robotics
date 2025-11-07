// # SPDX-FileCopyrightText: Alliander N. V.
//
// # SPDX-License-Identifier: Apache-2.0

#include <franka_msgs/action/grasp.hpp>
#include <franka_msgs/action/move.hpp>
#include <rcdt_messages/action/trigger.hpp>
#include <rclcpp/client.hpp>
#include <rclcpp/executors.hpp>
#include <rclcpp/node.hpp>
#include <rclcpp/utilities.hpp>
#include <rclcpp_action/client.hpp>
#include <rclcpp_action/client_goal_handle.hpp>
#include <rclcpp_action/rclcpp_action.hpp>
#include <std_srvs/srv/trigger.hpp>
#include <string>

typedef rcdt_messages::action::Trigger Trigger;
typedef franka_msgs::action::Move Move;
typedef franka_msgs::action::Grasp Grasp;

/** A node to control the actions of the gripper. */
class Gripper : public rclcpp::Node {
 public:
  Gripper();

 private:
  /** The action server to open the gripper. */
  rclcpp_action::Server<Trigger>::SharedPtr service_open;
  /** The action server to close the gripper. */
  rclcpp_action::Server<Trigger>::SharedPtr service_close;
  /** The action client to move the gripper. */
  rclcpp_action::Client<Move>::SharedPtr client_move;
  /** The action client to grasp with the gripper. */
  rclcpp_action::Client<Grasp>::SharedPtr client_grasp;

  /**
   * @brief Handle goal requests
   *
   * @param uuid
   * @param goal
   * @return rclcpp_action::GoalResponse
   */
  rclcpp_action::GoalResponse handle_goal(
      const rclcpp_action::GoalUUID& uuid,
      std::shared_ptr<const Trigger::Goal> goal);

  /**
   * @brief Handle cancel requests
   *
   * @param goal_handle
   * @return rclcpp_action::CancelResponse
   */
  rclcpp_action::CancelResponse handle_cancel(
      const std::shared_ptr<rclcpp_action::ServerGoalHandle<Trigger>>
          goal_handle);

  /**
   * @brief Handle accepted goals
   *
   * @param goal_handle
   * @param action_name
   */
  void handle_accepted(
      const std::shared_ptr<rclcpp_action::ServerGoalHandle<Trigger>>
          goal_handle,
      std::string action_name);

  /**
   * @brief Execute the action
   *
   * @param goal_handle
   * @param action_name
   * @return bool
   */
  bool execute(const std::shared_ptr<rclcpp_action::ServerGoalHandle<Trigger>>
                   goal_handle,
               std::string action_name);

  /**
   * @brief Open the gripper
   *
   * @param goal_handle
   */
  void open(const std::shared_ptr<rclcpp_action::ServerGoalHandle<Trigger>>
                goal_handle);

  /**
   * @brief Close the gripper
   *
   * @param goal_handle
   */
  void close(const std::shared_ptr<rclcpp_action::ServerGoalHandle<Trigger>>
                 goal_handle);
};
