// # SPDX-FileCopyrightText: Alliander N. V.
//
// # SPDX-License-Identifier: Apache-2.0

#include "fr3_gripper_simulation.hpp"

Fr3Gripper::Fr3Gripper() : Node("fr3_gripper") {
  std::string ns = this->get_namespace();
  std::string node_name = this->get_name();

  client = rclcpp_action::create_client<ParallelGripperCommand>(
      this, ns + "/gripper_action_controller/gripper_cmd");
  grasp_server = rclcpp_action::create_server<Grasp>(
      this, "~/grasp", std::bind(&Fr3Gripper::handle_goal<Grasp>, this, _1, _2),
      std::bind(&Fr3Gripper::handle_cancel<Grasp>, this, _1),
      std::bind(&Fr3Gripper::handle_accepted<Grasp>, this, _1));
  homing_server = rclcpp_action::create_server<Homing>(
      this, "~/homing",
      std::bind(&Fr3Gripper::handle_goal<Homing>, this, _1, _2),
      std::bind(&Fr3Gripper::handle_cancel<Homing>, this, _1),
      std::bind(&Fr3Gripper::handle_accepted<Homing>, this, _1));
  move_server = rclcpp_action::create_server<Move>(
      this, "~/move", std::bind(&Fr3Gripper::handle_goal<Move>, this, _1, _2),
      std::bind(&Fr3Gripper::handle_cancel<Move>, this, _1),
      std::bind(&Fr3Gripper::handle_accepted<Move>, this, _1));
};

template <typename action>
rclcpp_action::GoalResponse Fr3Gripper::handle_goal(
    const rclcpp_action::GoalUUID& uuid,
    std::shared_ptr<const typename action::Goal> goal) {
  RCLCPP_INFO(this->get_logger(), "Received goal request");
  (void)uuid;
  return rclcpp_action::GoalResponse::ACCEPT_AND_EXECUTE;
}

template <typename action>
rclcpp_action::CancelResponse Fr3Gripper::handle_cancel(
    const std::shared_ptr<rclcpp_action::ServerGoalHandle<action>>
        goal_handle) {
  RCLCPP_INFO(this->get_logger(), "Received request to cancel goal");
  (void)goal_handle;
  return rclcpp_action::CancelResponse::ACCEPT;
}

template <typename action>
void Fr3Gripper::handle_accepted(
    const std::shared_ptr<rclcpp_action::ServerGoalHandle<action>>
        goal_handle) {
  auto result = std::make_shared<typename action::Result>();
  std::thread(&Fr3Gripper::execute<action>, this, goal_handle).detach();
}

/**
 * @brief Execution for the Grasp action
 *
 * @param goal_handle
 */
template <>
void Fr3Gripper::execute<Grasp>(
    const std::shared_ptr<rclcpp_action::ServerGoalHandle<Grasp>> goal_handle) {
  auto goal = ParallelGripperCommand::Goal();
  goal.command.position = {respect_limits(goal_handle->get_goal()->width)};
  goal.command.effort = {goal_handle->get_goal()->force};

  send_goal(goal);

  auto result = std::make_shared<typename Grasp::Result>();
  auto success = true;
  if (rclcpp::ok()) {
    result->success = success;
    if (success) {
      goal_handle->succeed(result);
    } else {
      goal_handle->abort(result);
    }
  }
};

/**
 * @brief Execution for the Homing action
 *
 * @param goal_handle
 */
template <>
void Fr3Gripper::execute<Homing>(
    const std::shared_ptr<rclcpp_action::ServerGoalHandle<Homing>>
        goal_handle) {
  auto goal = ParallelGripperCommand::Goal();
  goal.command.position = {upper_limit};

  send_goal(goal);

  auto result = std::make_shared<typename Homing::Result>();
  auto success = true;
  if (rclcpp::ok()) {
    result->success = success;
    if (success) {
      goal_handle->succeed(result);
    } else {
      goal_handle->abort(result);
    }
  }
};

/**
 * @brief Execution for the Move action
 *
 * @param goal_handle
 */
template <>
void Fr3Gripper::execute<Move>(
    const std::shared_ptr<rclcpp_action::ServerGoalHandle<Move>> goal_handle) {
  auto goal = ParallelGripperCommand::Goal();
  goal.command.position = {respect_limits(goal_handle->get_goal()->width)};

  send_goal(goal);

  auto result = std::make_shared<typename Move::Result>();
  auto success = true;
  if (rclcpp::ok()) {
    result->success = success;
    if (success) {
      goal_handle->succeed(result);
    } else {
      goal_handle->abort(result);
    }
  }
};

bool Fr3Gripper::send_goal(const ParallelGripperCommand::Goal& goal) {
  auto future_goal_handle = client->async_send_goal(goal);
  if (future_goal_handle.wait_for(std::chrono::seconds(6)) ==
      std::future_status::timeout) {
    RCLCPP_ERROR(this->get_logger(), "Failed to obtain goal_handle. Timeout.");
    return false;
  }

  auto goal_handle = future_goal_handle.get();
  if (!goal_handle) {
    RCLCPP_ERROR(this->get_logger(), "Goal was rejected by the action server.");
    return false;
  }

  auto future_result = client->async_get_result(goal_handle);
  if (future_result.wait_for(std::chrono::seconds(5)) ==
      std::future_status::timeout) {
    RCLCPP_ERROR(this->get_logger(), "Failed to obtain result. Timeout.");
    return false;
  }

  return goal_reached(goal, *future_result.get().result);
}

double Fr3Gripper::respect_limits(double width) {
  return std::min(upper_limit, std::max(lower_limit, width));
}

bool Fr3Gripper::goal_reached(const ParallelGripperCommand::Goal& goal,
                              const ParallelGripperCommand::Result& result) {
  return result.reached_goal;
}

int main(int argc, char** argv) {
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<Fr3Gripper>());
  rclcpp::shutdown();
}
