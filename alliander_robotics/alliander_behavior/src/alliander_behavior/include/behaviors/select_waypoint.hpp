// # SPDX-FileCopyrightText: Alliander N. V.
//
// # SPDX-License-Identifier: Apache-2.0
#pragma once

#include <behaviortree_cpp/action_node.h>
#include <behaviortree_cpp/basic_types.h>

#include <cmath>
#include <rclcpp/rclcpp.hpp>

#include "behaviortree_cpp/tree_node.h"
#include "geographic_msgs/msg/geo_path.hpp"
#include "geometry_msgs/msg/quaternion.hpp"

class SelectWaypoint : public BT::SyncActionNode {
 public:
  SelectWaypoint(const std::string& name, const BT::NodeConfig& conf,
                 rclcpp::Node::SharedPtr node)
      : BT::SyncActionNode(name, conf),
        logger_(node->get_logger().get_child("GetWaypoint")) {}

  static BT::PortsList providedPorts() {
    return {BT::InputPort<geographic_msgs::msg::GeoPath>("route"),
            BT::InputPort<size_t>("waypoint_index"),
            BT::OutputPort<double>("latitude"),
            BT::OutputPort<double>("longitude"),
            BT::OutputPort<geometry_msgs::msg::Quaternion>("orientation")};
  }

  BT::NodeStatus tick() override {
    auto route = getInput<geographic_msgs::msg::GeoPath>("route");
    auto waypoint_index = getInput<size_t>("waypoint_index");
    if (!route || !waypoint_index) return BT::NodeStatus::FAILURE;

    auto index = waypoint_index.value();
    auto route_size = route->poses.size();
    if (index >= route_size) {
      RCLCPP_ERROR(logger_, "Waypoint index %zu is larger than route size %zu",
                   index, route_size);
      return BT::NodeStatus::FAILURE;
    }

    auto wp = route->poses.at(index);

    setOutput("latitude", wp.pose.position.latitude);
    setOutput("longitude", wp.pose.position.longitude);
    setOutput("orientation", wp.pose.orientation);
    return BT::NodeStatus::SUCCESS;
  }

 private:
  rclcpp::Logger logger_;
};
