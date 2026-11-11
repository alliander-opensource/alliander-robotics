// # SPDX-FileCopyrightText: Alliander N. V.
//
// # SPDX-License-Identifier: Apache-2.0
#pragma once

#include <behaviortree_ros2/bt_topic_sub_node.hpp>
#include <cmath>
#include <optional>
#include <rclcpp/logging.hpp>
#include <sensor_msgs/msg/battery_state.hpp>
#include <string>

namespace alliander_behavior {

/// Behavior that returns SUCCESS if battery percentage is below a threshold.
class IsBatteryBelow
    : public BT::RosTopicSubNode<sensor_msgs::msg::BatteryState> {
 public:
  /**
   * @brief initializes an IsBatteryBelow object.
   * @param name BT node name.
   * @param conf BT config, including port mappings.
   * @param params ROS2 context.
   */
  IsBatteryBelow(const std::string& name, const BT::NodeConfig& conf,
                 const BT::RosNodeParams& params)
      : BT::RosTopicSubNode<sensor_msgs::msg::BatteryState>(name, conf,
                                                            params) {}

  /**
   * @brief fills out BT.CPP ports list.
   * @return BT.CPP ports list.
   */
  static BT::PortsList providedPorts() {
    return providedBasicPorts(
        {BT::InputPort<double>("threshold", 0.25,
                               "Low if percentage <= this (0..1)"),
         BT::InputPort<double>("max_age_s", 5.0,
                               "Treat data older than this as low"),
         BT::InputPort<double>(
             "percentage_scale", 1.0,
             "Multiplier that maps the published percentage to 0..1")});
  }

  /**
   * @brief overrides tick() to check if battery message is valid, recent, and
   * has a percentage below a certain threshold.
   * @param msg BatteryState message to check.
   * @return status of this node: FAILURE if message is invalid, too old, or
   * above threshold, SUCCESS otherwise.
   */
  BT::NodeStatus onTick(
      const std::shared_ptr<sensor_msgs::msg::BatteryState>& msg) override {
    auto node = node_.lock();
    if (!node) return BT::NodeStatus::FAILURE;

    const auto now = node->now();
    if (!first_tick_) first_tick_ = now;

    if (!msg) {
      // no message yet: give the publisher some time after startup
      if ((now - *first_tick_).seconds() < startup_grace_s_) {
        RCLCPP_INFO_THROTTLE(logger(), *node->get_clock(), 2000,
                             "%s: waiting for first battery message",
                             name().c_str());
        return BT::NodeStatus::FAILURE;
      }
      RCLCPP_WARN_THROTTLE(logger(), *node->get_clock(), 5000,
                           "%s: no battery message received, assuming low",
                           name().c_str());
      return BT::NodeStatus::SUCCESS;
    }

    auto threshold = getInput<double>("threshold");
    auto max_age = getInput<double>("max_age_s");
    auto scale = getInput<double>("percentage_scale");
    if (!threshold || !max_age || !scale) {
      RCLCPP_ERROR(logger(), "%s: bad ports: %s", name().c_str(),
                   (!threshold ? threshold.error()
                    : !max_age ? max_age.error()
                               : scale.error())
                       .c_str());
      return BT::NodeStatus::FAILURE;
    }

    const double age = (now - rclcpp::Time(msg->header.stamp)).seconds();
    if (age > max_age.value()) {
      RCLCPP_WARN_THROTTLE(logger(), *node->get_clock(), 5000,
                           "%s: battery message is %.1f s old, assuming low",
                           name().c_str(), age);
      return BT::NodeStatus::SUCCESS;
    }

    if (std::isnan(msg->percentage)) {
      RCLCPP_WARN_THROTTLE(logger(), *node->get_clock(), 5000,
                           "%s: battery percentage is NaN, assuming low",
                           name().c_str());
      return BT::NodeStatus::SUCCESS;
    }

    const double percentage = msg->percentage * scale.value();
    return (percentage <= threshold.value()) ? BT::NodeStatus::SUCCESS
                                             : BT::NodeStatus::FAILURE;
  }

  /**
   * @brief always latch the last message.
   * @return true.
   */
  bool latchLastMessage() const override { return true; }

 private:
  /// Time instance indicating when node started.
  std::optional<rclcpp::Time> first_tick_;
  /// Grace period after which to fail because of no received battery messages.
  double startup_grace_s_ = 10.0;
};

}  // namespace alliander_behavior
