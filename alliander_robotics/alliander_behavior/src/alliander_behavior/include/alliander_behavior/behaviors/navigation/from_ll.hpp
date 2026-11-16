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

namespace alliander_behavior {

/// Class that calls the FromLL service to transform [lat, lon] to map frame
class FromLL : public BT::RosServiceNode<robot_localization::srv::FromLL> {
 public:
  /**
   * @brief initializes the FromLL service node.
   * @param name BT node name.
   * @param conf runtime config, port mappings, etc.
   * @param params ROS2 context for node.
   */
  FromLL(const std::string& name, const BT::NodeConfig& conf,
         const BT::RosNodeParams& params)
      : BT::RosServiceNode<robot_localization::srv::FromLL>(name, conf,
                                                            params) {}

  /**
   * @brief fills out BT.CPP's ports.
   * @return BT.CPP ports list.
   */
  static BT::PortsList providedPorts() {
    return providedBasicPorts(
        {BT::InputPort<double>("latitude"), BT::InputPort<double>("longitude"),
         BT::OutputPort<geometry_msgs::msg::Point>("map_point")});
  }

  /**
   * @brief creates a FromLL request.
   * @param request BT.ROS2 service request with the lat/lon input.
   * @return whether request is successfully created.
   */
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

  /**
   * @brief callback for when a response is received on the service call.
   * @param response BT.ROS2 service response with the converted map location.
   * @return status for this BT node.
   */
  BT::NodeStatus onResponseReceived(
      const Response::SharedPtr& response) override {
    setOutput("map_point", response->map_point);
    return BT::NodeStatus::SUCCESS;
  }

  /**
   * @brief override what to do on Node failre. In this case, log an error.
   * @param error the BT.ROS2 error to propagate.
   * @return status for this BT node.
   */
  BT::NodeStatus onFailure(BT::ServiceNodeErrorCode error) override {
    RCLCPP_ERROR(logger(), "FromLL error: %s", BT::toStr(error));
    return BT::NodeStatus::FAILURE;
  }
};

}  // namespace alliander_behavior
