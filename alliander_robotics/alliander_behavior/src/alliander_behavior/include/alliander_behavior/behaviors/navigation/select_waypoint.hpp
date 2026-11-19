// # SPDX-FileCopyrightText: Alliander N. V.
//
// # SPDX-License-Identifier: Apache-2.0
#pragma once

#include <behaviortree_cpp/action_node.h>

#include <cstddef>
#include <geographic_msgs/msg/geo_path.hpp>
#include <geometry_msgs/msg/quaternion.hpp>
#include <string>

namespace alliander_behavior {

/// Class that selects the next waypoint in a route.
class SelectWaypoint : public BT::SyncActionNode {
 public:
  /**
   * @brief initializes a SelectWaypoint object.
   * @param name BT node name.
   * @param conf BT node config.
   */
  SelectWaypoint(const std::string& name, const BT::NodeConfig& conf)
      : BT::SyncActionNode(name, conf) {}

  /**
   * @brief fills out the BT.CPP ports list.
   * @return BT ports list.
   */
  static BT::PortsList providedPorts() {
    return {BT::InputPort<geographic_msgs::msg::GeoPath>("route"),
            BT::InputPort<size_t>("waypoint_index"),
            BT::OutputPort<double>("latitude"),
            BT::OutputPort<double>("longitude"),
            BT::OutputPort<geometry_msgs::msg::Quaternion>("orientation")};
  }

  /**
   * @brief overrides standard tick() behavior, checking waypoint and route
   * bounds.
   * @return status for this BT node, indicating whether route & waypoint index
   * are correct.
   */
  BT::NodeStatus tick() override {
    auto route = getInput<geographic_msgs::msg::GeoPath>("route");
    auto waypoint_index = getInput<size_t>("waypoint_index");
    if (!route) {
      throw BT::RuntimeError(name() + ": bad port [route]: " + route.error());
    }
    if (!waypoint_index) {
      throw BT::RuntimeError(
          name() + ": bad port [waypoint_index]: " + waypoint_index.error());
    }

    const auto index = waypoint_index.value();
    if (index >= route->poses.size()) {
      return BT::NodeStatus::FAILURE;
    }

    const auto& wp = route->poses.at(index);
    setOutput("latitude", wp.pose.position.latitude);
    setOutput("longitude", wp.pose.position.longitude);
    setOutput("orientation", wp.pose.orientation);
    return BT::NodeStatus::SUCCESS;
  }
};

}  // namespace alliander_behavior
