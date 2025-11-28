// # SPDX-FileCopyrightText: Alliander N. V.
//
// # SPDX-License-Identifier: Apache-2.0

#include <rclcpp/executors/single_threaded_executor.hpp>

#include "rcdt_utilities/manipulate_pose.hpp"

int main(int argc, char** argv) {
  rclcpp::init(argc, argv);

  rclcpp::executors::SingleThreadedExecutor executor;
  auto node = std::make_shared<PoseManipulator>();
  executor.add_node(node);

  executor.spin();

  rclcpp::shutdown();
  return 0;
}
