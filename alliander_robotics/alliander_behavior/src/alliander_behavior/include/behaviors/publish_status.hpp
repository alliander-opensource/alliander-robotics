// # SPDX-FileCopyrightText: Alliander N. V.
//
// # SPDX-License-Identifier: Apache-2.0
#pragma once

#include <behaviortree_cpp/tree_node.h>

#include <behaviortree_ros2/bt_topic_pub_node.hpp>
#include <rclcpp/logger.hpp>
#include <rclcpp/logging.hpp>
#include <std_msgs/msg/string.hpp>

class PublishStatus : public BT::RosTopicPubNode<std_msgs::msg::String> {
 public:
  PublishStatus(const std::string& name, const BT::NodeConfig& conf,
                const BT::RosNodeParams& params)
      : BT::RosTopicPubNode<std_msgs::msg::String>(name, conf, params),
        logger_(params.nh.lock() ? params.nh.lock()->get_logger()
                                 : rclcpp::get_logger("PublishStatus")) {}

  static BT::PortsList providedPorts() {
    return providedBasicPorts(
        {BT::InputPort<std::string>("message", "Text to publish")});
  }

  bool setMessage(std_msgs::msg::String& msg) override {
    auto message = getInput<std::string>("message");

    if (!message) return false;

    msg.data = message.value();
    RCLCPP_INFO(logger_, "%s", msg.data.c_str());
    return true;
  }

 private:
  rclcpp::Logger logger_;
};
