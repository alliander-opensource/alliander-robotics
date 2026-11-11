// # SPDX-FileCopyrightText: Alliander N. V.
//
// # SPDX-License-Identifier: Apache-2.0
#pragma once

#include <behaviortree_ros2/bt_topic_pub_node.hpp>
#include <rclcpp/logging.hpp>
#include <std_msgs/msg/string.hpp>
#include <string>

namespace alliander_behavior {

/// Class that publishes a status message to ROS2 logs
class PublishStatus : public BT::RosTopicPubNode<std_msgs::msg::String> {
 public:
  /**
   * @brief initializes a PublishStatus object.
   * @param name BT node name.
   * @param conf BT config, including port mappings.
   * @param params ROS2 context.
   */
  PublishStatus(const std::string& name, const BT::NodeConfig& conf,
                const BT::RosNodeParams& params)
      : BT::RosTopicPubNode<std_msgs::msg::String>(name, conf, params) {}

  /**
   * @brief fills out the BT.CPP ports list.
   * @return BT.CPP ports list.
   */
  static BT::PortsList providedPorts() {
    return providedBasicPorts(
        {BT::InputPort<std::string>("message", "Text to publish")});
  }

  /**
   * @brief overrides message creation.
   * @param msg the string message to publish.
   * @return false if port is faulty, true otherwise.
   */
  bool setMessage(std_msgs::msg::String& msg) override {
    auto message = getInput<std::string>("message");
    if (!message) {
      RCLCPP_ERROR(node_->get_logger(), "%s: bad port: %s", name().c_str(),
                   message.error().c_str());
      return false;
    }
    msg.data = message.value();
    RCLCPP_INFO(node_->get_logger(), "%s", msg.data.c_str());
    return true;
  }
};

}  // namespace alliander_behavior
