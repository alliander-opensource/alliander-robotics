// # SPDX-FileCopyrightText: Alliander N. V.
//
// # SPDX-License-Identifier: Apache-2.0
#pragma once

#include <behaviortree_cpp/action_node.h>
#include <behaviortree_cpp/basic_types.h>
#include <behaviortree_cpp/tree_node.h>

#include "geometry_msgs/msg/point.hpp"
#include "geometry_msgs/msg/pose_stamped.hpp"
#include "geometry_msgs/msg/quaternion.hpp"

namespace alliander_behavior {

/// Class to create a PoseStamped out of a given Point in map frame.
/// This class does not use BT.ROS2 as it can be purely BT.CPP.
class MakePose : public BT::SyncActionNode {
 public:
  /**
   * @brief initializes the MakePose object.
   * @param name the BT node name.
   * @param conf BT config holding port mappings, runtime config, etc.
   */
  MakePose(const std::string& name, const BT::NodeConfig& conf)
      : BT::SyncActionNode(name, conf) {}

  /**
   * @brief fills out the BT ports.
   * @return BT.CPP ports list.
   */
  static BT::PortsList providedPorts() {
    return {BT::InputPort<geometry_msgs::msg::Point>("point"),
            BT::InputPort<geometry_msgs::msg::Quaternion>("orientation"),
            BT::InputPort<std::string>("frame_id"),
            BT::OutputPort<geometry_msgs::msg::PoseStamped>("pose")};
  }

  /**
   * @brief overrides standard tick() behavior. Creates a
   * PoseStamped from a Point.
   * @return status for this node.
   */
  BT::NodeStatus tick() override {
    auto map_point = getInput<geometry_msgs::msg::Point>("point");
    auto orientation = getInput<geometry_msgs::msg::Quaternion>("orientation");
    auto frame_id = getInput<std::string>("frame_id");

    if (!map_point || !orientation || !frame_id) return BT::NodeStatus::FAILURE;

    geometry_msgs::msg::PoseStamped pose;
    pose.header.frame_id = frame_id.value();
    pose.pose.position = map_point.value();
    pose.pose.orientation = orientation.value();
    setOutput("pose", pose);

    return BT::NodeStatus::SUCCESS;
  }
};

}  // namespace alliander_behavior
