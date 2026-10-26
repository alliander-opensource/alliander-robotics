// # SPDX-FileCopyrightText: Alliander N. V.
//
// # SPDX-License-Identifier: Apache-2.0

#include <behaviortree_cpp/bt_factory.h>

#include <behaviortree_ros2/bt_action_node.hpp>
#include <is_battery_low.hpp>
#include <rclcpp/rclcpp.hpp>

// NB: naming of TaskPlanner according to BT2 ROS documentation
class TaskPlanner {
 public:
  TaskPlanner(rclcpp::Node::SharedPtr node, const std::string& xml_path)
      : node_(std::move(node)) {
    BT::RosNodeParams params;
    params.nh = node_;  // if we make TaskPlanner inherit from rclcpp::Node, we
                        // get an ugly shared_from_this() here
    params.default_port_value = "battery_state";

    // register all behaviors here
    factory_.registerNodeType<IsBatteryLow>("IsBatteryLow", params);

    tree_ = factory_.createTreeFromFile(xml_path);
  }

  BT::NodeStatus tick() { return tree_.tickOnce(); }

 private:
  rclcpp::Node::SharedPtr node_;
  BT::BehaviorTreeFactory factory_;
  BT::Tree tree_;
};
