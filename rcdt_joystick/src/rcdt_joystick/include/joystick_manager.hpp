// # SPDX-FileCopyrightText: Alliander N. V.
//
// # SPDX-License-Identifier: Apache-2.0

#ifndef JOYSTICK_MANAGER_HPP_
#define JOYSTICK_MANAGER_HPP_

#include <cstdint>
#include <geometry_msgs/msg/twist_stamped.hpp>
#include <rcdt_interfaces/action/trigger_action.hpp>
#include <rcdt_interfaces/srv/string_srv.hpp>
#include <rclcpp/client.hpp>
#include <rclcpp/node.hpp>
#include <rclcpp/node_options.hpp>
#include <rclcpp/rclcpp.hpp>
#include <rclcpp_action/client.hpp>
#include <rclcpp_action/rclcpp_action.hpp>
#include <sensor_msgs/msg/joy.hpp>
#include <std_srvs/srv/trigger.hpp>

using std::placeholders::_1;
using std::placeholders::_2;
typedef rcdt_interfaces::action::TriggerAction TriggerAction;

enum Button {
  A = 0,   // Switch between platform modes
  B = 1,   // Move arm back to home position
  X = 2,   // Trigger E-stop
  Y = 3,   // Reset E-stop
  LT = 9,  // Open gripper
  RT = 10  // Close gripper
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

  void handle_buttons_arm(const std::vector<int32_t>& buttons);

  void handle_buttons_vehicle(const std::vector<int32_t>& buttons);

  /**
   * @brief Check whether a button has been pressed or not.
   */
  bool check_btn_pressed(size_t idx, const std::vector<int32_t>& curr,
                         const std::vector<int32_t>& prev);

  /**
   * @brief publish TwistStamped message based on linear and angular value.
   */
  void handle_driving(const float& linear, const float& angular);

  /**
   * @brief publish TwistStamped message based on [x, y, z] translation and a
   * rotation value.
   */
  void handle_arm_movement(const float& x, const float& y, const float& z,
                           const float& rotation);

  void move_arm_to_home();

  void send_trigger_request(
      const rclcpp::Client<std_srvs::srv::Trigger>::SharedPtr& client);

  void send_gripper_goal(
      const rclcpp_action::Client<TriggerAction>::SharedPtr& client);
  void gripper_goal_response_callback(
      std::shared_ptr<rclcpp_action::ClientGoalHandle<TriggerAction>>
          goal_handle);
  void gripper_feedback_callback(
      std::shared_ptr<rclcpp_action::ClientGoalHandle<TriggerAction>>,
      const std::shared_ptr<const TriggerAction::Feedback> feedback);
  void gripper_result_callback(
      rclcpp_action::ClientGoalHandle<TriggerAction>::WrappedResult& result);

  rclcpp::Node::SharedPtr node;
  rclcpp::Subscription<sensor_msgs::msg::Joy>::SharedPtr sub_joy;
  rclcpp::Publisher<geometry_msgs::msg::TwistStamped>::SharedPtr pub_arm_vel;
  rclcpp::Publisher<geometry_msgs::msg::TwistStamped>::SharedPtr
      pub_vehicle_vel;
  rclcpp::Client<std_srvs::srv::Trigger>::SharedPtr srv_client_estop_trigger;
  rclcpp::Client<std_srvs::srv::Trigger>::SharedPtr srv_client_estop_reset;
  rclcpp::Client<rcdt_interfaces::srv::StringSrv>::SharedPtr srv_client_arm_home;
  rclcpp_action::Client<TriggerAction>::SharedPtr action_client_gripper_open;
  rclcpp_action::Client<TriggerAction>::SharedPtr action_client_gripper_close;

  std::string arm_topic;
  std::string arm_frame_id;
  std::string vehicle_topic;

  sensor_msgs::msg::Joy::SharedPtr prev_joy_input;

  static constexpr int arm_mode = 0;
  static constexpr int vehicle_mode = 1;
  int current_mode = arm_mode;
  bool gripper_busy = false;

  const float dead_axis_zone =
      0.3;  // Make response to changes in joystick values less sensitive.
};

#endif  // JOYSTICK_MANAGER_HPP_
