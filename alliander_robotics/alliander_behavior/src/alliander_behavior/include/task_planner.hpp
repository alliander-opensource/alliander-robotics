// # SPDX-FileCopyrightText: Alliander N. V.
//
// # SPDX-License-Identifier: Apache-2.0

#include <behaviortree_cpp/bt_factory.h>

#include <algorithm>
#include <behaviortree_ros2/bt_action_node.hpp>
#include <call_trigger_action.hpp>
#include <filesystem>
#include <go_to_waypoint.hpp>
#include <is_battery_below.hpp>
#include <rclcpp/rclcpp.hpp>
#include <vector>

namespace fs = std::filesystem;

// NB: naming of TaskPlanner according to BT2 ROS documentation
class TaskPlanner {
 public:
  TaskPlanner(rclcpp::Node::SharedPtr node, const std::string& tree_name,
              const std::string& config_dir)
      : node_(std::move(node)) {
    BT::RosNodeParams params;
    params.nh = node_;  // if we make TaskPlanner inherit from rclcpp::Node, we
                        // get an ugly shared_from_this() here
    params.default_port_value = "battery_state";

    // register all behaviors here
    factory_.registerNodeType<IsBatteryBelow>("IsBatteryLow", params);
    factory_.registerNodeType<CallTriggerAction>("DockRobot", params);
    factory_.registerNodeType<GoToWaypoint>("GoToWaypoint", params);

    // load all trees and subtrees
    fs::path bt_dir = config_dir;
    registerTreesFromDirectory(fs::path(bt_dir));
    registerTreesFromDirectory(fs::path(bt_dir) / "subtrees");

    tree_ = factory_.createTree(tree_name);

    RCLCPP_INFO(node_->get_logger(), "Loaded Behavior Tree with name %s",
                tree_name.c_str());
  }

  BT::NodeStatus tick() { return tree_.tickOnce(); }

 private:
  void registerTreesFromDirectory(const fs::path& dir) {
    std::vector<fs::path> files;
    for (const auto& entry : fs::directory_iterator(dir)) {
      if (entry.is_regular_file() && entry.path().extension() == ".xml") {
        files.push_back(entry.path());
      }
    }

    std::sort(files.begin(), files.end());

    for (const auto& file : files) {
      factory_.registerBehaviorTreeFromFile(file.string());
    }
  }

  rclcpp::Node::SharedPtr node_;
  BT::BehaviorTreeFactory factory_;
  BT::Tree tree_;
};
