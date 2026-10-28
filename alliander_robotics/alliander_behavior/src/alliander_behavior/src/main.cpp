#include <behaviortree_cpp/basic_types.h>

#include <chrono>

#include "task_planner.hpp"

int main(int argc, char* argv[]) {
  rclcpp::init(argc, argv);
  auto node = std::make_shared<rclcpp::Node>("task_planner");

  node->declare_parameter<std::string>("tree_name", "PatrolAndCharge");
  TaskPlanner task_planner(node, node->get_parameter("tree_name").as_string(),
                           node->get_parameter("config_dir").as_string());

  auto timer = node->create_wall_timer(std::chrono::milliseconds(100), [&] {
    const auto status = task_planner.tick();
    if (status != BT::NodeStatus::RUNNING) {
      RCLCPP_WARN(node->get_logger(),
                  "Task Planner tree finished with status %s",
                  BT::toStr(status).c_str());
    }
  });

  rclcpp::spin(node);
  rclcpp::shutdown();
  return 0;
}
