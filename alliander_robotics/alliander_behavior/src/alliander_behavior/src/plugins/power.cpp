// # SPDX-FileCopyrightText: Alliander N. V.
//
// # SPDX-License-Identifier: Apache-2.0

#include <alliander_behavior/behaviors/power/is_battery_below.hpp>
#include <behaviortree_ros2/plugins.hpp>

BT_REGISTER_ROS_NODES(factory, params) {
  auto battery = params;
  battery.default_port_value = "battery_status";
  factory.registerNodeType<alliander_behavior::IsBatteryBelow>("IsBatteryBelow",
                                                               battery);
}
