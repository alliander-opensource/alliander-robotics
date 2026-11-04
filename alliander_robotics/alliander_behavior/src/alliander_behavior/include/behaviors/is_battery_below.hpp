// # SPDX-FileCopyrightText: Alliander N. V.
//
// # SPDX-License-Identifier: Apache-2.0
#pragma once

#include <behaviortree_cpp/basic_types.h>

#include <behaviortree_ros2/bt_topic_sub_node.hpp>
#include <cmath>
#include <rclcpp/logging.hpp>
#include <sensor_msgs/msg/battery_state.hpp>

#include "behaviortree_cpp/tree_node.h"
#include "sensor_msgs/msg/battery_state.hpp"

class IsBatteryBelow
    : public BT::RosTopicSubNode<sensor_msgs::msg::BatteryState> {
 public:
  IsBatteryBelow(const std::string& name, const BT::NodeConfig& conf,
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
    auto node = node_.lock();

    if (!node) return BT::NodeStatus::FAILURE;

    // ignore no messages for X seconds when starting up to avoid race
    // conditions
    const auto now = node->now();
    if (!first_tick_) first_tick_ = now;

    if (!msg) {
      if ((now - *first_tick_).seconds() < startup_grace_s_) {
        RCLCPP_INFO_THROTTLE(
            logger(), *node->get_clock(), 2000,
            "IsBatteryBelow: waiting for first battery message");
        return BT::NodeStatus::FAILURE;
      }
      RCLCPP_WARN_THROTTLE(
          logger(), *node_.lock()->get_clock(), 5000,
          "IsBatteryBelow: no battery message received, assuming low");
      return BT::NodeStatus::SUCCESS;
    }

    auto threshold = getInput<double>("threshold");
    auto max_age = getInput<double>("max_age_s");

    if (!threshold || !max_age) {
      RCLCPP_ERROR(logger(), "IsBatteryBelow: bad ports: %s",
                   (!threshold ? threshold.error() : max_age.error()).c_str());
    }

    const double age =
        (node->now() - rclcpp::Time(msg->header.stamp)).seconds();
    if (age > max_age.value()) {
      // stale message: assume low
      return BT::NodeStatus::SUCCESS;
    }

    // NaN value: assume low
    if (std::isnan(msg->percentage)) {
      return BT::NodeStatus::SUCCESS;
    }

    // Normalize battery percentage to work with
    // Husarion (0..1) and Gazebo LinearBatteryPlugin (0..100)
    double percentage = normalizeBatteryPercentage(msg->percentage);

    return (percentage <= threshold.value()) ? BT::NodeStatus::SUCCESS
                                             : BT::NodeStatus::FAILURE;
  }

  double normalizeBatteryPercentage(double raw) {
    return (raw > 1.0) ? raw / 100.0 : raw;
  }

  bool latchLastMessage() const override { return true; }

 private:
  std::optional<rclcpp::Time> first_tick_;
  double startup_grace_s_ = 10.0;
};
