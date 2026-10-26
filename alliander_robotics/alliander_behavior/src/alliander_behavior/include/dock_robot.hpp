#pragma once

#include <behaviortree_cpp/basic_types.h>

#include <behaviortree_ros2/bt_topic_sub_node.hpp>
#include <cmath>

#include "behaviortree_cpp/tree_node.h"

class DockRobot : public BT::RosTopicSubNode<sensor_msgs::msg::BatteryState> {
 public:
  DockRobot(const std::string& name, const BT::NodeConfig& conf,
            const BT::RosNodeParams& params)
      : BT::RosTopicSubNode<sensor_msgs::msg::BatteryState>(name, conf,
                                                            params) {}

  static BT::PortsList providedPorts() {
    return providedBasicPorts(
        {BT::InputPort<double>("threshold", 0.25,
                               "Low if percentage <= this (0..1)"),
         BT::InputPort<double>("max_age_s", 5.0,
                               "Treat data older than this as low")});
  }

  BT::NodeStatus onTick(
      const std::shared_ptr<sensor_msgs::msg::BatteryState>& msg) override {
    if (!msg) {
      return BT::NodeStatus::SUCCESS;
    }

    const double threshold = getInput<double>("threshold").value();
    const double max_age = getInput<double>("max_age_s").value();

    if (auto node = node_.lock()) {
      const double age =
          (node->now() - rclcpp::Time(msg->header.stamp)).seconds();
      if (age > max_age) {
        // stale message: assume low
        return BT::NodeStatus::SUCCESS;
      }
    }

    // NaN value: assume low
    if (std::isnan(msg->percentage)) {
      return BT::NodeStatus::SUCCESS;
    }

    return (msg->percentage <= threshold) ? BT::NodeStatus::SUCCESS
                                          : BT::NodeStatus::FAILURE;
  }
};
