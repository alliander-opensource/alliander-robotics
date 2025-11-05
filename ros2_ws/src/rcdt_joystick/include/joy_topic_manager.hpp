// # SPDX-FileCopyrightText: Alliander N. V.
//
// # SPDX-License-Identifier: Apache-2.0

#include <ament_index_cpp/get_package_share_directory.hpp>
#include <fstream>
#include <nlohmann/json.hpp>
#include <rclcpp/executors.hpp>
#include <rclcpp/node.hpp>
#include <sensor_msgs/msg/joy.hpp>

using std::placeholders::_1;
using std::placeholders::_2;

using json = nlohmann::json;
using Joy = sensor_msgs::msg::Joy;

/// Struct that links joystick buttons to topics.
struct Button {
  /// Joystick button key.
  int key;
  /// Topic to publish on.
  std::string topic;
  /// Service to publish on.
  std::string service;
  /// Joystick button state.
  int state = -1;
};

/// Class to send joystick button commands to ROS topics.
class JoyTopicManager : public rclcpp::Node {
 public:
  /// ROS package name.
  std::string package = "rcdt_joystick";
  /// Config file name.
  std::string file_name = "/config/gamepad_mapping.json";
  /// Constructor.
  JoyTopicManager();

 private:
  /// HashMap between button keys and Button structs.
  std::map<int, Button> buttons;

  /// Subscription to joystick messages.
  rclcpp::Subscription<Joy>::SharedPtr subscription_joy;
  /**
   * @brief Joystick message callback.
   * @param msg Joystick message.
   */
  void callback_joy(Joy msg);

  /// Converts JSON config file to Buttons.
  void read_json();
  /**
   * @brief Add a Button based on JSON config.
   * @param json JSON snippet detailing button key and topic/service.
   */
  void add_button(json json);
};
