// # SPDX-FileCopyrightText: Alliander N. V.
//
// # SPDX-License-Identifier: Apache-2.0

#include <behaviortree_cpp/blackboard.h>
#include <behaviortree_cpp/bt_factory.h>

#include <behaviors/call_trigger_action.hpp>
#include <behaviors/from_ll.hpp>
#include <behaviors/go_to_waypoint.hpp>
#include <behaviors/is_battery_below.hpp>
#include <behaviors/load_route.hpp>
#include <behaviors/make_pose.hpp>
#include <behaviors/publish_status.hpp>
#include <behaviors/select_waypoint.hpp>
#include <behaviortree_ros2/bt_action_node.hpp>
#include <filesystem>
#include <geographic_msgs/msg/geo_path.hpp>
#include <rclcpp/rclcpp.hpp>
#include <rclcpp/service.hpp>
#include <rclcpp/subscription.hpp>
#include <status_logger.hpp>
#include <std_srvs/srv/trigger.hpp>

namespace fs = std::filesystem;

class AutonomousNavigationBT {
 public:
  explicit AutonomousNavigationBT(rclcpp::Node::SharedPtr node);

  BT::NodeStatus tick() { return tree_.tickOnce(); }

 private:
  void registerTreesFromDirectory(const fs::path& dir);
  void waypointsCallback(const geographic_msgs::msg::GeoPath::SharedPtr msg);
  void stopNavCallback(
      const std::shared_ptr<std_srvs::srv::Trigger::Request> request,
      std::shared_ptr<std_srvs::srv::Trigger::Response> response);

  rclcpp::Node::SharedPtr node_;
  BT::BehaviorTreeFactory factory_;
  BT::Tree tree_;
  std::unique_ptr<RosStatusLogger> status_logger_;
  BT::Blackboard::Ptr bb_;

  rclcpp::Subscription<geographic_msgs::msg::GeoPath>::SharedPtr sub_waypoints_;
  rclcpp::Service<std_srvs::srv::Trigger>::SharedPtr srv_stop_nav_;
};
