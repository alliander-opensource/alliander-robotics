// # SPDX-FileCopyrightText: Alliander N. V.
//
// # SPDX-License-Identifier: Apache-2.0

#include "imu_bridge.hpp"

ImuBridge::ImuBridge() : Node("imu_bridge") {
  sub_accel = this->create_subscription<geometry_msgs::msg::Vector3Stamped>(
      "/topic_in_linear_acceleration", 1,
      [this](const geometry_msgs::msg::Vector3Stamped msg) {
        this->latest_accel_msg = msg;
        this->publish_imu();
      });

  sub_ang_vel = this->create_subscription<geometry_msgs::msg::Vector3Stamped>(
      "/topic_in_angular_velocity", 1,
      [this](const geometry_msgs::msg::Vector3Stamped msg) {
        this->latest_ang_vel_msg = msg;
      });

  pub_imu = this->create_publisher<sensor_msgs::msg::Imu>("/topic_out_imu", 1);
}

void ImuBridge::publish_imu() {
  sensor_msgs::msg::Imu msg;
  msg.header.stamp = this->latest_accel_msg.header.stamp;
  msg.header.frame_id = this->latest_accel_msg.header.frame_id;

  msg.linear_acceleration = this->latest_accel_msg.vector;
  msg.angular_velocity = this->latest_ang_vel_msg.vector;

  pub_imu->publish(msg);
}
