// # SPDX-FileCopyrightText: Alliander N. V.
//
// # SPDX-License-Identifier: Apache-2.0

#include "gripper.hpp"

using std::placeholders::_1;
using std::placeholders::_2;

Gripper::Gripper() : Node("gripper") {
  std::string ns = this->get_namespace();
  std::string node_name = this->get_name();

  client_move =
      rclcpp_action::create_client<Move>(this, ns + "/fr3_gripper/move");
  client_grasp =
      rclcpp_action::create_client<Grasp>(this, ns + "/fr3_gripper/grasp");
  service_open = rclcpp_action::create_server<Trigger>(
      this, ns + "/" + node_name + "/open",
      std::bind(&Gripper::handle_goal, this, _1, _2),
      std::bind(&Gripper::handle_cancel, this, _1),
      std::bind(&Gripper::handle_accepted, this, _1, "open"));
  service_close = rclcpp_action::create_server<Trigger>(
      this, ns + "/" + node_name + "/close",
      std::bind(&Gripper::handle_goal, this, _1, _2),
      std::bind(&Gripper::handle_cancel, this, _1),
      std::bind(&Gripper::handle_accepted, this, _1, "close"));
};

rclcpp_action::GoalResponse Gripper::handle_goal(
    const rclcpp_action::GoalUUID& uuid,
    std::shared_ptr<const Trigger::Goal> goal) {
  RCLCPP_INFO(this->get_logger(), "Received goal request");
  (void)uuid;
  return rclcpp_action::GoalResponse::ACCEPT_AND_EXECUTE;
}

rclcpp_action::CancelResponse Gripper::handle_cancel(
    const std::shared_ptr<rclcpp_action::ServerGoalHandle<Trigger>>
        goal_handle) {
  RCLCPP_INFO(this->get_logger(), "Received request to cancel goal");
  (void)goal_handle;
  return rclcpp_action::CancelResponse::ACCEPT;
}

void Gripper::handle_accepted(
    const std::shared_ptr<rclcpp_action::ServerGoalHandle<Trigger>> goal_handle,
    std::string action_name) {
  auto result = std::make_shared<typename Trigger::Result>();
  if (action_name == "open") {
    std::thread{std::bind(&Gripper::open, this, goal_handle)}.detach();
  } else if (action_name == "close") {
    std::thread{std::bind(&Gripper::close, this, goal_handle)}.detach();
  }
}

void Gripper::open(
    std::shared_ptr<rclcpp_action::ServerGoalHandle<Trigger>> goal_handle) {
  auto goal = Move::Goal();
  goal.width = 0.08;
  goal.speed = 0.03;
  auto future_goal_handle = client_move->async_send_goal(goal);
  if (future_goal_handle.wait_for(std::chrono::seconds(5)) ==
      std::future_status::timeout) {
    RCLCPP_ERROR(this->get_logger(), "Failed to obtain goal_handle. Timeout.");
    return;
  }

  auto future_result = client_move->async_get_result(future_goal_handle.get());
  if (future_result.wait_for(std::chrono::seconds(5)) ==
      std::future_status::timeout) {
    RCLCPP_ERROR(this->get_logger(), "Failed to obtain result. Timeout.");
    return;
  }

  auto result = std::make_shared<typename Trigger::Result>();
  auto success =
      future_result.get().code == rclcpp_action::ResultCode::SUCCEEDED;

  if (rclcpp::ok()) {
    result->success = success;
    if (success) {
      goal_handle->succeed(result);
    } else {
      goal_handle->abort(result);
    }
  }
};

void Gripper::close(
    std::shared_ptr<rclcpp_action::ServerGoalHandle<Trigger>> goal_handle) {
  auto goal = Grasp::Goal();
  goal.width = 0.0;
  goal.force = 100.0;
  goal.speed = 0.03;
  auto future_goal_handle = client_grasp->async_send_goal(goal);
  if (future_goal_handle.wait_for(std::chrono::seconds(5)) ==
      std::future_status::timeout) {
    RCLCPP_ERROR(this->get_logger(), "Failed to obtain goal_handle. Timeout.");
    return;
  }

  auto future_result = client_grasp->async_get_result(future_goal_handle.get());
  if (future_result.wait_for(std::chrono::seconds(5)) ==
      std::future_status::timeout) {
    RCLCPP_ERROR(this->get_logger(), "Failed to obtain result. Timeout.");
    return;
  }

  auto result = std::make_shared<typename Trigger::Result>();
  auto success =
      future_result.get().code == rclcpp_action::ResultCode::SUCCEEDED;

  if (rclcpp::ok()) {
    result->success = success;
    if (success) {
      goal_handle->succeed(result);
    } else {
      goal_handle->abort(result);
    }
  }
};

int main(int argc, char** argv) {
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<Gripper>());
  rclcpp::shutdown();
}
