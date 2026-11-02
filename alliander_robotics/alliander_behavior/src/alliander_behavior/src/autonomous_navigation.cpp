// # SPDX-FileCopyrightText: Alliander N. V.
//
// # SPDX-License-Identifier: Apache-2.0
#include "autonomous_navigation.hpp"

#include <behaviortree_cpp/basic_types.h>

#include <chrono>
#include <rclcpp/logging.hpp>
#include <rclcpp/qos.hpp>

#include "behaviors/publish_status.hpp"
#include "behaviors/select_waypoint.hpp"
#include "geographic_msgs/msg/geo_path.hpp"

AutonomousNavigationBT::AutonomousNavigationBT(rclcpp::Node::SharedPtr node)
    : node_(std::move(node)) {
  node_->declare_parameter<std::string>("tree_name", "");
  auto tree_name = node_->get_parameter("tree_name").as_string();
  node_->declare_parameter<std::string>("config_dir", "");
  auto config_dir = node_->get_parameter("config_dir").as_string();

  node_->declare_parameter<int>("charge_timeout_ms", 6000000);
  node_->declare_parameter<int>("server_timeout_ms", 10000);
  node_->declare_parameter<double>("battery_threshold_low", 0.25);
  node_->declare_parameter<double>("battery_threshold_charged", 0.90);

  node_->declare_parameter<std::string>("waypoints_topic", "/waypoints_topic");
  node_->declare_parameter<std::string>("battery_topic", "/battery_topic");
  node_->declare_parameter<std::string>("dock_action", "/dock_robot");
  node_->declare_parameter<std::string>("undock_action", "/undock_robot");
  node_->declare_parameter<std::string>("navigate_to_pose_action",
                                        "navigate_to_pose");
  node_->declare_parameter<std::string>("fromll_service", "/fromLL");
  node_->declare_parameter<std::string>("status_topic", "/status_topic");

  auto waypoints_topic = node_->get_parameter("waypoints_topic").as_string();

  // stub for unimplemented behavior. TODO: remove
  auto stub = [this](const std::string& id) {
    return [this, id](BT::TreeNode&) {
      RCLCPP_WARN_THROTTLE(node_->get_logger(), *node_->get_clock(), 5000,
                           "%s: not implemented yet, returning SUCCESS",
                           id.c_str());
      return BT::NodeStatus::SUCCESS;
    };
  };

  BT::RosNodeParams params;
  params.nh = node_;
  params.wait_for_server_timeout = std::chrono::milliseconds(
      node_->get_parameter("server_timeout_ms").as_int());
  params.default_port_value = node_->get_parameter("battery_topic").as_string();
  factory_.registerNodeType<IsBatteryBelow>("IsBatteryBelow", params);

  // params.default_port_value =
  // node_->get_parameter("dock_action").as_string();

  // factory_.registerNodeType<CallTriggerAction>("DockRobot", params);

  // Placeholders
  factory_.registerSimpleAction("DockRobot", stub("DockRobot"));
  factory_.registerSimpleAction("UndockRobot", stub("UndockRobot"));

  params.default_port_value =
      node_->get_parameter("navigate_to_pose_action").as_string();
  factory_.registerNodeType<GoToWaypoint>("GoToWaypoint", params);

  // params.default_port_value =
  // node_->get_parameter("undock_action").as_string();
  // factory_.registerNodeType<CallTriggerAction>("UndockRobot", params);

  // receiving new route
  factory_.registerNodeType<LoadRoute>("LoadRoute");

  // patrol behaviors
  factory_.registerNodeType<SelectWaypoint>("SelectWaypoint", node_);

  params.default_port_value =
      node_->get_parameter("fromll_service").as_string();
  factory_.registerNodeType<FromLL>("FromLL", params);
  factory_.registerNodeType<MakePose>("MakePose");

  params.default_port_value = node_->get_parameter("status_topic").as_string();
  factory_.registerNodeType<PublishStatus>("PublishStatus", params);

  // load all trees and subtrees
  fs::path bt_dir = config_dir;
  registerTreesFromDirectory(fs::path(bt_dir));
  registerTreesFromDirectory(fs::path(bt_dir) / "subtrees");

  tree_ = factory_.createTree(tree_name);

  // Blackboard
  bb_ = tree_.rootBlackboard();
  bb_->set("has_new_route", false);
  bb_->set("pending_route", geographic_msgs::msg::GeoPath{});
  bb_->set<unsigned>("timeout_ms",
                     static_cast<unsigned>(
                         node_->get_parameter("charge_timeout_ms").as_int()));
  bb_->set<double>("battery_threshold_low",
                   node_->get_parameter("battery_threshold_low").as_double());
  bb_->set<double>(
      "battery_threshold_charged",
      node_->get_parameter("battery_threshold_charged").as_double());

  // ROS inits
  sub_waypoints_ = node_->create_subscription<geographic_msgs::msg::GeoPath>(
      waypoints_topic, rclcpp::QoS(1).reliable().transient_local(),
      [this](const geographic_msgs::msg::GeoPath::SharedPtr msg) {
        waypointsCallback(msg);
      });

  RCLCPP_INFO(node_->get_logger(), "Loaded Behavior Tree with name %s",
              tree_name.c_str());
}

void AutonomousNavigationBT::registerTreesFromDirectory(const fs::path& dir) {
  // this could be moved to a common hpp file if we include more BT types
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

void AutonomousNavigationBT::waypointsCallback(
    const geographic_msgs::msg::GeoPath::SharedPtr msg) {
  if (msg->poses.empty()) {
    RCLCPP_WARN(node_->get_logger(), "Ignoring empty route");
    return;
  }

  // this will trigger the LoadRoute behavior on next tick
  bb_->set("pending_route", *msg);
  bb_->set("has_new_route", true);
}

int main(int argc, char* argv[]) {
  rclcpp::init(argc, argv);
  auto node = std::make_shared<rclcpp::Node>("autonomous_navigation_bt");
  AutonomousNavigationBT autonomous_navigation_bt(node);

  auto timer = node->create_wall_timer(std::chrono::milliseconds(100), [&] {
    const auto status = autonomous_navigation_bt.tick();
    if (status != BT::NodeStatus::RUNNING) {
      RCLCPP_WARN(node->get_logger(),
                  "Autonomous Navigation tree finished with status %s",
                  BT::toStr(status).c_str());
    }
  });

  rclcpp::spin(node);
  rclcpp::shutdown();
  return 0;
}
