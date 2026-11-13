// # SPDX-FileCopyrightText: Alliander N. V.
//
// # SPDX-License-Identifier: Apache-2.0
#include <atomic>
#include <chrono>
#include <csignal>
#include <rclcpp/rclcpp.hpp>
#include <thread>

#include "alliander_behavior/behavior_executor.hpp"

const uint16_t SHUTDOWN_SLEEP_PERIOD_MS = 100;

// Handle shutdown ourselves, so that actions can be cancelled
// before everything gets taken down by ROS. This way the robot
// will stop moving to its goal when the system goes down.
std::atomic<bool> g_shutdown_requested{false};

void onSignal(int) { g_shutdown_requested = true; }

int main(int argc, char* argv[]) {
  rclcpp::init(argc, argv, rclcpp::InitOptions(),
               rclcpp::SignalHandlerOptions::None);
  std::signal(SIGINT, onSignal);
  std::signal(SIGTERM, onSignal);

  auto node = std::make_shared<rclcpp::Node>("behavior_executor");
  auto executor = std::make_unique<alliander_behavior::BehaviorExecutor>(node);

  // Spin ROS node separately
  rclcpp::executors::SingleThreadedExecutor ros_executor;
  ros_executor.add_node(node);
  std::thread spin_thread([&ros_executor]() { ros_executor.spin(); });

  // Catch interrupt here separately
  while (!g_shutdown_requested && rclcpp::ok()) {
    std::this_thread::sleep_for(
        std::chrono::milliseconds(SHUTDOWN_SLEEP_PERIOD_MS));
  }

  RCLCPP_INFO(node->get_logger(), "Shutting down, halting the running tree");
  if (!executor->haltAndWait(std::chrono::seconds(5))) {
    RCLCPP_WARN(node->get_logger(), "Tree did not halt within 5 s");
  }

  ros_executor.cancel();
  spin_thread.join();
  rclcpp::shutdown();
  return 0;
}
