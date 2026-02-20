// # SPDX-FileCopyrightText: Alliander N. V.
//
// # SPDX-License-Identifier: Apache-2.0

#include <sys/resource.h>

#include <rclcpp/executors/multi_threaded_executor.hpp>
#include <rclcpp/node_options.hpp>

#include "joystick_manager.hpp"

int main(int argc, char** argv) {
  rclcpp::init(argc, argv);
  rclcpp::NodeOptions node_options;
  node_options.automatically_declare_parameters_from_overrides(true);
  rclcpp::Node::SharedPtr node =
      std::make_shared<rclcpp::Node>("alliander_joystick", node_options);
  JoystickManager joystick_manager(node);
  rclcpp::executors::MultiThreadedExecutor executor;
  executor.add_node(node);
  executor.spin();

  rclcpp::shutdown();
  return 0;
}
