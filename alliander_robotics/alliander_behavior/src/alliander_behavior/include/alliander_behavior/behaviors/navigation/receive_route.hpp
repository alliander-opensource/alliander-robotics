// # SPDX-FileCopyrightText: Alliander N. V.
//
// # SPDX-License-Identifier: Apache-2.0
#pragma once

#include <behaviortree_ros2/bt_topic_sub_node.hpp>
#include <cstddef>
#include <geographic_msgs/msg/geo_path.hpp>
#include <string>

namespace alliander_behavior {

/// Class that handles incoming GPS routes.
class ReceiveRoute : public BT::RosTopicSubNode<geographic_msgs::msg::GeoPath> {
 public:
  /**
   * @brief initializes the ReceiveRoute object.
   * @param name BT node name.
   * @param conf BT node config with port mappings, runtime config, etc.
   * @param params ROS2 context for BT.ROS2.
   */
  ReceiveRoute(const std::string& name, const BT::NodeConfig& conf,
               const BT::RosNodeParams& params)
      : BT::RosTopicSubNode<geographic_msgs::msg::GeoPath>(name, conf, params) {
  }

  /**
   * @brief fills out the BT.CPP input/output ports.
   * @return BT.CPP ports list.
   */
  static BT::PortsList providedPorts() {
    return providedBasicPorts(
        {BT::OutputPort<geographic_msgs::msg::GeoPath>("route"),
         BT::OutputPort<size_t>("route_size")});
  }

  /**
   * @brief overrides standard onTick() behavior. Checks whether the route is
   * admissable and sets some blackboard state.
   * @param msg incoming GPS waypoints.
   * @return status for this BT node.
   */
  BT::NodeStatus onTick(
      const std::shared_ptr<geographic_msgs::msg::GeoPath>& msg) override {
    if (!msg) return BT::NodeStatus::FAILURE;
    if (msg->poses.empty()) {
      RCLCPP_WARN(logger(), "%s: ignoring empty route", name().c_str());
      return BT::NodeStatus::FAILURE;
    }
    RCLCPP_INFO(logger(), "%s: received route with %zu waypoints",
                name().c_str(), msg->poses.size());
    setOutput("route", *msg);
    setOutput("route_size", msg->poses.size());
    return BT::NodeStatus::SUCCESS;
  }
};

}  // namespace alliander_behavior
