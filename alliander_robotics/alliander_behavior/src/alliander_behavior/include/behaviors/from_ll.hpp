// # SPDX-FileCopyrightText: Alliander N. V.
//
// # SPDX-License-Identifier: Apache-2.0
#pragma once

#include <behaviortree_cpp/basic_types.h>

#include <behaviortree_ros2/bt_service_node.hpp>
#include <geometry_msgs/msg/point.hpp>
#include <rclcpp/logging.hpp>
#include <rclcpp/type_support_decl.hpp>
#include <robot_localization/srv/from_ll.hpp>

#include "robot_localization/srv/from_ll.hpp"

class FromLL : public BT::RosServiceNode<robot_localization::srv::FromLL> {
 public:
  FromLL(const std::string& name, const BT::NodeConfig& conf,
         const BT::RosNodeParams& params)
      : BT::RosServiceNode<robot_localization::srv::FromLL>(name, conf,
                                                            params) {}

  static BT::PortsList providedPorts() {
    return providedBasicPorts(
        {BT::InputPort<double>("latitude"), BT::InputPort<double>("longitude"),
         BT::OutputPort<geometry_msgs::msg::Point>("map_point")});
  }

  bool setRequest(Request::SharedPtr& request) override {
    auto lat = getInput<double>("latitude");
    auto lon = getInput<double>("longitude");

    if (!lat || !lon) {
      RCLCPP_ERROR(logger(), "FromLL: bad ports: %s",
                   (!lat ? lat.error() : lon.error()).c_str());
      return false;
    }

    request->ll_point.latitude = lat.value();
    request->ll_point.longitude = lon.value();
    request->ll_point.altitude = 0.0;
    return true;
  }

  BT::NodeStatus onResponseReceived(
      const Response::SharedPtr& response) override {
    setOutput("map_point", response->map_point);
    return BT::NodeStatus::SUCCESS;
  }

  BT::NodeStatus onFailure(BT::ServiceNodeErrorCode error) override {
    RCLCPP_ERROR(logger(), "FromLL error: %s", BT::toStr(error));
    return BT::NodeStatus::FAILURE;
  }
};
