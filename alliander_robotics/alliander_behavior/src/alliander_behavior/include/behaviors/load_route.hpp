// # SPDX-FileCopyrightText: Alliander N. V.
//
// # SPDX-License-Identifier: Apache-2.0
#pragma once

#include <behaviortree_cpp/action_node.h>
#include <behaviortree_cpp/basic_types.h>

#include <cmath>

#include "behaviortree_cpp/tree_node.h"
#include "geographic_msgs/msg/geo_path.hpp"

class LoadRoute : public BT::SyncActionNode {
 public:
  LoadRoute(const std::string& name, const BT::NodeConfig& conf)
      : BT::SyncActionNode(name, conf) {}

  static BT::PortsList providedPorts() {
    return {BT::InputPort<geographic_msgs::msg::GeoPath>("pending"),
            BT::OutputPort<geographic_msgs::msg::GeoPath>("route"),
            BT::OutputPort<size_t>("route_size"),
            BT::OutputPort<size_t>("waypoint_index"),
            BT::OutputPort<bool>("has_new_route")};
  }

  BT::NodeStatus tick() override {
    auto pending = getInput<geographic_msgs::msg::GeoPath>("pending");
    if (!pending) return BT::NodeStatus::FAILURE;
    setOutput("route", pending.value());
    setOutput("waypoint_index", 0UL);
    setOutput("route_size", pending.value().poses.size());
    setOutput("has_new_route", false);
    return BT::NodeStatus::SUCCESS;
  }
};
