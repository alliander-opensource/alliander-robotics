// # SPDX-FileCopyrightText: Alliander N. V.
//
// # SPDX-License-Identifier: Apache-2.0
#pragma once

#include <behaviortree_cpp/basic_types.h>
#include <behaviortree_cpp/condition_node.h>

#include <atomic>
#include <behaviortree_ros2/ros_node_params.hpp>
#include <memory>
#include <rclcpp/rclcpp.hpp>
#include <rclcpp/service.hpp>
#include <std_srvs/srv/trigger.hpp>
#include <string>

#include "std_srvs/srv/trigger.hpp"

namespace alliander_behavior {

/// Class that handles receiving std_srvs::Trigger service requests.
class TriggerReceived : public BT::ConditionNode {
 public:
  /**
   * @brief initializes a TriggerReceived object.
   * @param name BT node name.
   * @param conf BT config such as port mappings.
   * @param params ROS2 context.
   */
  TriggerReceived(const std::string& name, const BT::NodeConfig& conf,
                  const BT::RosNodeParams& params)
      : BT::ConditionNode(name, conf) {
    std::string service_name;
    if (!getInput("service_name", service_name) || service_name.empty()) {
      service_name = params.default_port_value;
    }
    if (service_name.empty()) {
      throw BT::RuntimeError(name + ": no service_name, check XML");
    }
    auto node = params.nh.lock();
    if (!node) {
      throw BT::RuntimeError(name + ": failed to initialize ROS node");
    }

    server_ = node->create_service<std_srvs::srv::Trigger>(
        service_name,
        [this](const std::shared_ptr<std_srvs::srv::Trigger::Request>,
               std::shared_ptr<std_srvs::srv::Trigger::Response> response) {
          has_new_request_.store(true);

          response->success = true;
          response->message = "Request received";
        });
  }

  /**
   * @brief fills out BT.CPP ports list.
   * @return BT.CPP ports list.
   */
  static BT::PortsList providedPorts() {
    return {BT::InputPort<std::string>("service_name",
                                       "Name of std_srvs/srv/Trigger server")};
  }

  /**
   * @brief overrides tick by returning SUCCESS only if a new request is in.
   * @return status for this node.
   */
  BT::NodeStatus tick() override {
    if (has_new_request_.exchange(false)) {
      return BT::NodeStatus::SUCCESS;
    }

    return BT::NodeStatus::FAILURE;
  }

 private:
  /// Server to receive Trigger requests on.
  rclcpp::Service<std_srvs::srv::Trigger>::SharedPtr server_;
  /// Atomic (because of multithreading) bool indicating whether a new request
  /// is received.
  std::atomic_bool has_new_request_{false};
};

}  // namespace alliander_behavior
