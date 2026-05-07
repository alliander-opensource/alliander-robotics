// # SPDX-FileCopyrightText: Alliander N. V.
//
// # SPDX-License-Identifier: Apache-2.0

#include "imu_bridge.hpp"

int main(int argc, char** argv) {
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<ImuBridge>());
  rclcpp::shutdown();
  return 0;
}
