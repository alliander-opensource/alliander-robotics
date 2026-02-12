// # SPDX-FileCopyrightText: Alliander N. V.
//
// # SPDX-License-Identifier: Apache-2.0

#include "joystick_manager.hpp"

JoystickManager::JoystickManager(rclcpp::Node::SharedPtr node) : node(node) {
  arm_topic = node->get_parameter("arm_cmd_topic").as_string();
  arm_frame_id = node->get_parameter("arm_frame_id").as_string();
  arm_gripper_name = node->get_parameter("arm_gripper_name").as_string();
  arm_home_service = node->get_parameter("arm_home_service").as_string();
  vehicle_topic = node->get_parameter("vehicle_cmd_topic").as_string();
  vehicle_estop_reset_service =
      node->get_parameter("vehicle_estop_reset").as_string();
  vehicle_estop_trigger_service =
      node->get_parameter("vehicle_estop_trigger").as_string();

  initialize_joystick_manager();

  RCLCPP_INFO(node->get_logger(), "Joystick Manager initialized.");
};

JoystickManager::~JoystickManager() {
  // Make sure that the arm's and vehicle's motion are stoppped
  pub_arm_vel->publish(geometry_msgs::msg::TwistStamped{});
  pub_vehicle_vel->publish(geometry_msgs::msg::TwistStamped{});
  RCLCPP_INFO(node->get_logger(), "Shutdown complete.");
}

void JoystickManager::initialize_joystick_manager() {
  // Subscibers
  sub_joy = node->create_subscription<sensor_msgs::msg::Joy>(
      "/joy", rclcpp::SensorDataQoS(),
      std::bind(&JoystickManager::joy_cb, this, _1));

  // Publishers
  pub_arm_vel =
      node->create_publisher<geometry_msgs::msg::TwistStamped>(arm_topic, 10);
  pub_vehicle_vel = node->create_publisher<geometry_msgs::msg::TwistStamped>(
      vehicle_topic, 10);

  // Service clients
  srv_client_estop_trigger = node->create_client<std_srvs::srv::Trigger>(
      vehicle_estop_trigger_service);
  srv_client_estop_reset =
      node->create_client<std_srvs::srv::Trigger>(vehicle_estop_reset_service);
  srv_client_arm_home =
      node->create_client<rcdt_interfaces::srv::StringSrv>(arm_home_service);

  // Action clients
  action_client_gripper_open = rclcpp_action::create_client<TriggerAction>(
      node, arm_gripper_name + "/open");
  action_client_gripper_close = rclcpp_action::create_client<TriggerAction>(
      node, arm_gripper_name + "/close");

  // Log initial mode
  switch (current_mode) {
    case arm_mode:
      RCLCPP_INFO(node->get_logger(), "Initial mode: ARM mode.");
      break;
    case vehicle_mode:
      RCLCPP_INFO(node->get_logger(), "Initial mode: VEHICLE mode.");
      break;
    case no_mode:
      RCLCPP_INFO(
          node->get_logger(),
          "Initial mode: NO MODE, press 'A'/CROSS to switch to ARM mode.");
      break;
    default:
      RCLCPP_ERROR(node->get_logger(), "Unknown platform mode.");
      break;
  }

  prev_joy_input = std::make_shared<sensor_msgs::msg::Joy>();
}

void JoystickManager::joy_cb(const sensor_msgs::msg::Joy::SharedPtr msg) {
  // First message: only store and return
  if (!prev_joy_input || prev_joy_input->buttons.empty()) {
    prev_joy_input = msg;
    return;
  }

  // First handle joystick input since e.g. and e-stop trigger should have
  // hightest priority.
  handle_button_input(msg->buttons);

  switch (current_mode) {
    case arm_mode && !arm_busy:  // Don't send arm messages while it's already
                                 // following a trajectory
      handle_arm_movement(msg->axes[1], msg->axes[0], msg->axes[3],
                          msg->axes[2]);
      break;
    case vehicle_mode:
      handle_driving(msg->axes[1], msg->axes[0]);
      break;
    case no_mode:
      // Don't do anything.
      break;
    default:
      RCLCPP_ERROR(node->get_logger(), "Unknown platform mode.");
      break;
  }

  // Store current message as previous for next callback
  prev_joy_input = msg;
}

void JoystickManager::handle_button_input(const std::vector<int32_t>& buttons) {
  // Switch between platform modes
  if (check_btn_pressed(Button::A, buttons, prev_joy_input->buttons)) {
    switch (current_mode) {
      case arm_mode:
        RCLCPP_INFO(node->get_logger(), "Switch to VEHICLE mode.");
        current_mode = vehicle_mode;
        pub_arm_vel->publish(geometry_msgs::msg::TwistStamped{});
        return;
      case vehicle_mode:
        RCLCPP_INFO(node->get_logger(), "Switch to ARM mode.");
        current_mode = arm_mode;
        pub_vehicle_vel->publish(geometry_msgs::msg::TwistStamped{});
        return;
      case no_mode:
        RCLCPP_INFO(node->get_logger(), "Switch to ARM mode.");
        current_mode = arm_mode;
        return;
      default:
        RCLCPP_ERROR(node->get_logger(), "Unknown platform mode.");
        return;
    }
  }

  // Mode-specific behaviour
  switch (current_mode) {
    case arm_mode:
      handle_buttons_arm(buttons);
      return;
    case vehicle_mode:
      handle_buttons_vehicle(buttons);
      return;
    case no_mode:
      // Don't do anything.
      return;
    default:
      RCLCPP_ERROR(node->get_logger(), "Unknown platform mode.");
      return;
  }
}

void JoystickManager::handle_buttons_arm(const std::vector<int32_t>& buttons) {
  // Open gripper
  if (check_btn_pressed(Button::LT, buttons, prev_joy_input->buttons) &&
      !gripper_busy) {
    RCLCPP_INFO(node->get_logger(), "Open gripper");
    send_gripper_goal(action_client_gripper_open);
  }

  // Close gripper
  if (check_btn_pressed(Button::RT, buttons, prev_joy_input->buttons) &&
      !gripper_busy) {
    RCLCPP_INFO(node->get_logger(), "Close gripper");
    send_gripper_goal(action_client_gripper_close);
  }

  // Move back home
  if (check_btn_pressed(Button::B, buttons, prev_joy_input->buttons)) {
    RCLCPP_INFO(node->get_logger(), "Move back to home position");
    move_arm_to_home();
  }
}

void JoystickManager::handle_buttons_vehicle(
    const std::vector<int32_t>& buttons) {
  // Trigger E-stop
  if (check_btn_pressed(Button::X, buttons, prev_joy_input->buttons)) {
    RCLCPP_INFO(node->get_logger(), "Trigger E-stop");
    send_trigger_request(srv_client_estop_trigger);
  }

  // Reset E-stop
  if (check_btn_pressed(Button::Y, buttons, prev_joy_input->buttons)) {
    RCLCPP_INFO(node->get_logger(), "Reset E-stop");
    send_trigger_request(srv_client_estop_reset);
  }
}

bool JoystickManager::check_btn_pressed(size_t idx,
                                        const std::vector<int32_t>& curr,
                                        const std::vector<int32_t>& prev) {
  return curr[idx] != prev[idx];
}

void JoystickManager::handle_driving(const float& linear,
                                     const float& angular) {
  float prev_angular = prev_joy_input->axes[0];
  float prev_linear = prev_joy_input->axes[1];

  geometry_msgs::msg::TwistStamped twist;
  twist.header.stamp = node->now();
  twist.header.frame_id = "base_link";

  // Forward/backward
  twist.twist.linear.x = (std::abs(linear) > dead_axis_zone)
                             ? (linear * vehicle_speed_scale)
                             : 0.0;

  // Turning
  twist.twist.angular.z = (std::abs(angular) > dead_axis_zone)
                              ? (angular * vehicle_speed_scale)
                              : 0.0;

  pub_vehicle_vel->publish(twist);
}

void JoystickManager::handle_arm_movement(const float& x, const float& y,
                                          const float& z,
                                          const float& rotation) {
  geometry_msgs::msg::TwistStamped twist;
  twist.header.stamp = node->now();
  twist.header.frame_id = arm_frame_id;

  twist.twist.linear.x = (std::abs(x) > dead_axis_zone)
                             ? (x * arm_speed_scale)
                             : 0.0;  // Forward/backward
  twist.twist.linear.y = (std::abs(y) > dead_axis_zone) ? (y * arm_speed_scale)
                                                        : 0.0;  // Left/right
  twist.twist.linear.z =
      (std::abs(z) > dead_axis_zone) ? (z * arm_speed_scale) : 0.0;  // Up/down

  // Turning
  twist.twist.angular.z =
      (std::abs(rotation) > dead_axis_zone) ? rotation : 0.0;

  pub_arm_vel->publish(twist);
}

void JoystickManager::move_arm_to_home() {
  // Prevent retriggering while already running
  if (arm_busy) {
    RCLCPP_INFO(node->get_logger(), "Arm already moving.");
    return;
  }

  arm_busy = true;

  auto request = std::make_shared<rcdt_interfaces::srv::StringSrv::Request>();
  request->text = "home";

  if (!srv_client_arm_home->service_is_ready()) {
    RCLCPP_WARN(node->get_logger(), "'Move arm' service not available.");
    arm_busy = false;
    return;
  }

  srv_client_arm_home->async_send_request(
      request,
      [this](rclcpp::Client<rcdt_interfaces::srv::StringSrv>::SharedFuture
                 future) {
        try {
          auto response = future.get();

          if (response->success) {
            RCLCPP_INFO(node->get_logger(), "Arm moved home successfully.");
          } else {
            RCLCPP_WARN(node->get_logger(), "Move home failed.");
          }
        } catch (const std::exception& e) {
          RCLCPP_ERROR(node->get_logger(), "'Move arm' service call failed: %s",
                       e.what());
        }

        // Unblock arm once service call finishes
        arm_busy = false;
      });
}

void JoystickManager::send_trigger_request(
    const rclcpp::Client<std_srvs::srv::Trigger>::SharedPtr& client) {
  auto trigger_request = std::make_shared<std_srvs::srv::Trigger::Request>();

  if (!client->service_is_ready()) {
    RCLCPP_WARN(node->get_logger(), "Trigger service not available.");
    arm_busy = false;
    return;
  }

  client->async_send_request(
      trigger_request,
      [this](rclcpp::Client<std_srvs::srv::Trigger>::SharedFuture future) {
        try {
          auto response = future.get();

          if (response->success) {
            RCLCPP_INFO(node->get_logger(), "Trigger service successful.");
          } else {
            RCLCPP_WARN(node->get_logger(), "Trigger service failed.");
          }
        } catch (const std::exception& e) {
          RCLCPP_ERROR(node->get_logger(), "Trigger service call failed: %s",
                       e.what());
        }
      });
}

void JoystickManager::send_gripper_goal(
    const rclcpp_action::Client<TriggerAction>::SharedPtr& client) {
  gripper_busy = true;
  auto trigger_action_goal =
      std::make_shared<rcdt_interfaces::action::TriggerAction::Goal>();
  RCLCPP_INFO(node->get_logger(), "Sending goal");

  auto send_goal_options =
      rclcpp_action::Client<TriggerAction>::SendGoalOptions();

  send_goal_options.goal_response_callback = [this](auto goal_handle) {
    this->gripper_goal_response_callback(goal_handle);
  };

  send_goal_options.feedback_callback = [this](auto goal_handle,
                                               auto feedback) {
    this->gripper_feedback_callback(goal_handle, feedback);
  };

  send_goal_options.result_callback = [this](auto result) {
    this->gripper_result_callback(result);
  };
  client->async_send_goal(*trigger_action_goal, send_goal_options);
}

void JoystickManager::gripper_goal_response_callback(
    std::shared_ptr<rclcpp_action::ClientGoalHandle<TriggerAction>>
        goal_handle) {
  if (!goal_handle) {
    RCLCPP_ERROR(node->get_logger(), "Goal was rejected");
    gripper_busy = false;
  } else {
    RCLCPP_INFO(node->get_logger(), "Goal accepted");
  }
}

void JoystickManager::gripper_feedback_callback(
    std::shared_ptr<rclcpp_action::ClientGoalHandle<TriggerAction>>,
    const std::shared_ptr<const TriggerAction::Feedback> feedback) {
  RCLCPP_INFO(node->get_logger(), "Open gripper status: %s",
              feedback->status.c_str());
}

void JoystickManager::gripper_result_callback(
    rclcpp_action::ClientGoalHandle<TriggerAction>::WrappedResult& result) {
  switch (result.code) {
    case rclcpp_action::ResultCode::SUCCEEDED:
      RCLCPP_INFO(node->get_logger(), "Goal was succeeded");
      break;
    case rclcpp_action::ResultCode::ABORTED:
      RCLCPP_ERROR(node->get_logger(), "Goal was aborted");
      break;
    case rclcpp_action::ResultCode::CANCELED:
      RCLCPP_ERROR(node->get_logger(), "Goal was canceled");
      break;
    default:
      RCLCPP_ERROR(node->get_logger(), "Unknown result code");
      break;
  }
  gripper_busy = false;
}
