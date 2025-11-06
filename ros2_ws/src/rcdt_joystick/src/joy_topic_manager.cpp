// # SPDX-FileCopyrightText: Alliander N. V.
//
// # SPDX-License-Identifier: Apache-2.0

#include "rcdt_joystick/joy_topic_manager.hpp"

JoyTopicManager::JoyTopicManager() : Node("joy_topic_manager") {
  this->declare_parameter("joy_topic", "/joy");
  auto joy_topic = this->get_parameter("joy_topic").as_string();

  subscription_joy = this->create_subscription<Joy>(
      "/joy", 10, std::bind(&JoyTopicManager::callback_joy, this, _1));

  read_json();
};

void JoyTopicManager::callback_joy(Joy msg) {
  for (auto& [index, button] : buttons) {
    auto state = msg.buttons[index];
    if (button.state == -1) {
      button.state = state;
    }
    if (state == button.state) {
      continue;
    }
    button.state = state;
  }
}

void JoyTopicManager::read_json() {
  auto file = ament_index_cpp::get_package_share_directory(package) + file_name;
  std::ifstream f(file);
  json data = json::parse(f);

  if (!data.is_array()) {
    RCLCPP_WARN(this->get_logger(), "Invalid JSON format, expected an array.");
    return;
  };

  for (const auto& item : data) {
    add_button(item);
  }
  for (const auto& [k, v] : buttons)
    std::cout << "m[" << k << "] = (" << v.topic << ", " << v.service << ") "
              << std::endl;
}

void JoyTopicManager::add_button(json json) {
  Button button{};

  if (json.contains("button")) {
    if (json.contains("button")) {
      if (json["button"].is_number_integer()) {
        button.key = json["button"].get<int>();
      } else {
        RCLCPP_WARN(this->get_logger(),
                    "Invalid value for key 'button', expected integer.");
        return;
      }
    } else {
      RCLCPP_WARN(this->get_logger(), "The key 'button' was expected in JSON.");
      return;
    }
  }

  if (json.contains("topic")) {
    if (json["topic"].is_string()) {
      button.topic = json["topic"].get<std::string>();
      buttons.insert({button.key, button});
      return;
    } else {
      RCLCPP_WARN(this->get_logger(),
                  "Invalid value for key 'topic', expected string.");
      return;
    }
  }

  if (json.contains("service")) {
    if (json["service"].is_string()) {
      button.service = json["service"].get<std::string>();
      buttons.insert({button.key, button});
      return;
    } else {
      RCLCPP_WARN(this->get_logger(),
                  "Invalid value for key 'service', expected string.");
      return;
    }
  }

  RCLCPP_WARN(this->get_logger(),
              "A key 'topic' or 'service' was expected in JSON.");
}
