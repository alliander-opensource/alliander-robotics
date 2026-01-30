// # SPDX-FileCopyrightText: Alliander N. V.
//
// # SPDX-License-Identifier: Apache-2.0

#include "rcdt_joystick/joystick_manager.hpp"

JoystickManager::JoystickManager(rclcpp::Node::SharedPtr node)
    : node(node) {
  // arm_topic = this->get_parameter("arm_cmd_topic").as_string();
  // arm_frame_id = this->get_parameter("arm_frame_id").as_string();
  // vehicle_topic = this->get_parameter("vehicle_cmd_topic").as_string();
  initialize_joystick_manager();
};

JoystickManager::~JoystickManager() {
  // Make sure that the arm's and vehicle's motion are stoppped
  pub_arm_vel->publish(geometry_msgs::msg::TwistStamped{});
  pub_vehicle_vel->publish(geometry_msgs::msg::TwistStamped{});
  RCLCPP_INFO(node->get_logger(), "Shutdown complete.");
}

void JoystickManager::initialize_joystick_manager(){

  // Subscibers
  sub_joy = node->create_subscription<sensor_msgs::msg::Joy>(
    "/joy",
    rclcpp::SensorDataQoS(),
    std::bind(&JoystickManager::joy_cb, this, _1)
  );

  // Publishers
  pub_arm_vel = node->create_publisher<geometry_msgs::msg::TwistStamped>(
    arm_topic, 
    10
  );
  pub_vehicle_vel = node->create_publisher<geometry_msgs::msg::TwistStamped>(
    vehicle_topic, 
    10
  );

  switch(current_mode){
    case arm_mode:
      RCLCPP_INFO(node->get_logger(), "Initial mode: ARM mode.");
      break;
    case vehicle_mode:
      RCLCPP_INFO(node->get_logger(), "Initial mode: VEHICLE mode.");
      break;
    default:
      RCLCPP_ERROR(node->get_logger(), "Unknown platform mode.");
      break;
  }

  prev_joy_input = std::make_shared<sensor_msgs::msg::Joy>();

  RCLCPP_INFO(node->get_logger(), "Joystick Manager initialized.");
}

void JoystickManager::joy_cb(const sensor_msgs::msg::Joy::SharedPtr msg) {
  // First message: just store and return
  if (!prev_joy_input || prev_joy_input->buttons.empty()) {
    prev_joy_input = msg;
    return;
  }

  handle_button_input(msg->buttons);

  switch(current_mode){
    case arm_mode:
      handle_arm_movement(msg->axes[1], msg->axes[0], msg->axes[3], msg->axes[2]);
      break;
    case vehicle_mode:
      handle_driving(msg->axes[1], msg->axes[0]);
      break;
    default:
      RCLCPP_ERROR(node->get_logger(), "Unknown platform mode.");
      break;
  }

  // Store current message as previous for next callback
  prev_joy_input = msg;
}

void JoystickManager::handle_button_input(const std::vector<int32_t>& buttons) {
  int32_t btn_change_platform = buttons[0];  // A
  int32_t btn_estop_trigger = buttons[2];    // X
  int32_t btn_estop_reset = buttons[3];      // Y

  // Don't do anything when the button's value hasn't changed.
  if (prev_joy_input->buttons[0] != btn_change_platform){
    switch(current_mode){
      case arm_mode:
        RCLCPP_INFO(node->get_logger(), "Switch to VEHICLE mode.");
        current_mode = vehicle_mode;
        pub_arm_vel->publish(geometry_msgs::msg::TwistStamped{});
        break;
      case vehicle_mode:
        RCLCPP_INFO(node->get_logger(), "Switch to ARM mode.");
        current_mode = arm_mode;
        pub_vehicle_vel->publish(geometry_msgs::msg::TwistStamped{});
        break;
      default:
        RCLCPP_ERROR(node->get_logger(), "Unknown platform mode.");
        break;
    }
  }
}

void JoystickManager::handle_driving(const float& linear, const float& angular) {
  float prev_angular = prev_joy_input->axes[0];
  float prev_linear = prev_joy_input->axes[1];

  // Only act if something changed, TODO: do the husarions need a constant stream of input?
  // if (angular == prev_angular && linear == prev_linear) {
  //   return;
  // }

  geometry_msgs::msg::TwistStamped twist;
  twist.header.stamp = node->now();
  twist.header.frame_id = "base_link";

  // Forward/backward
  twist.twist.linear.x = (std::abs(linear) > dead_axis_zone) ? linear : 0.0;

  // Turning
  twist.twist.angular.z = (std::abs(angular) > dead_axis_zone) ? angular : 0.0;

  pub_vehicle_vel->publish(twist);
}

void JoystickManager::handle_arm_movement(const float& x, const float& y, const float& z, const float& rotation) {
  geometry_msgs::msg::TwistStamped twist;
  twist.header.stamp = node->now();
  twist.header.frame_id = arm_frame_id;

  twist.twist.linear.x = (std::abs(x) > dead_axis_zone) ? x : 0.0;  // Forward/backward
  twist.twist.linear.y = (std::abs(y) > dead_axis_zone) ? y : 0.0;  // Left/right
  twist.twist.linear.z = (std::abs(z) > dead_axis_zone) ? z : 0.0;  // Up/down

  // Turning
  twist.twist.angular.z = (std::abs(rotation) > dead_axis_zone) ? rotation : 0.0;  // TODO: I want to rotate just joint7, this does not work

  pub_arm_vel->publish(twist);
}
