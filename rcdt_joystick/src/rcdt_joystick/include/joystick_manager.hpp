// # SPDX-FileCopyrightText: Alliander N. V.
//
// # SPDX-License-Identifier: Apache-2.0

#ifndef JOYSTICK_MANAGER_HPP_
#define JOYSTICK_MANAGER_HPP_

#include <cstdint>
#include <rclcpp/node.hpp>
#include <rclcpp/node_options.hpp>
#include <rclcpp/rclcpp.hpp>
#include <geometry_msgs/msg/twist_stamped.hpp>
#include <sensor_msgs/msg/joy.hpp>

using std::placeholders::_1;
using std::placeholders::_2;

struct Button {
  int key_id;
  int key_value;
};

/// Class to interact with the joystick.
class JoystickManager {
 public:
  /**
   * @brief constructor for the JoystickManager class.
   * @param node The ROS2 node to attach to.
   */
  JoystickManager(rclcpp::Node::SharedPtr node);
  ~JoystickManager();

 private:

  /**
    * @brief initialize the joystick manager.
    */
  void initialize_joystick_manager();

  /**
   * @brief callback method that handles the data received from the joystick.
   */
  void joy_cb(const sensor_msgs::msg::Joy::SharedPtr msg);

  /**
   * @brief based on the button input, activate corresponding behaviour.
   */
  void handle_button_input(const std::vector<int32_t>& buttons);

  /**
   * @brief publish TwistStamped message based on linear and angular value. 
   */
  void handle_driving(const float& linear, const float& angular);

  /**
   * @brief publish TwistStamped message based on [x, y, z] translation and a rotation value.
   */
  void handle_arm_movement(const float& x, const float& y, const float& z, const float& rotation);

  rclcpp::Node::SharedPtr node;
  rclcpp::Subscription<sensor_msgs::msg::Joy>::SharedPtr sub_joy;
  rclcpp::Publisher<geometry_msgs::msg::TwistStamped>::SharedPtr pub_arm_vel;
  rclcpp::Publisher<geometry_msgs::msg::TwistStamped>::SharedPtr pub_vehicle_vel;

  std::string arm_topic;
  std::string arm_frame_id;
  std::string vehicle_topic;

  sensor_msgs::msg::Joy::SharedPtr prev_joy_input;

  static constexpr int arm_mode = 0;
  static constexpr int vehicle_mode = 1;
  int current_mode = arm_mode;

  const float dead_axis_zone = 0.3;  // Make response to changes in joystick values less sensitive.

};

#endif  // JOYSTICK_MANAGER_HPP_