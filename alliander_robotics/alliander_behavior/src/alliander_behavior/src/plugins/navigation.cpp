// # SPDX-FileCopyrightText: Alliander N. V.
//
// # SPDX-License-Identifier: Apache-2.0

#include <alliander_behavior/behaviors/navigation/from_ll.hpp>
#include <alliander_behavior/behaviors/navigation/make_pose.hpp>
#include <alliander_behavior/behaviors/navigation/navigate_to_pose.hpp>
#include <alliander_behavior/behaviors/navigation/receive_route.hpp>
#include <alliander_behavior/behaviors/navigation/select_waypoint.hpp>
#include <behaviortree_ros2/plugins.hpp>

BT_REGISTER_ROS_NODES(factory, params) {
  using namespace alliander_behavior;

  auto with_default = [&params](const std::string& name) {
    auto p = params;
    p.default_port_value = name;
    return p;
  };

  factory.registerNodeType<NavigateToPose>("NavigateToPose",
                                           with_default("navigate_to_pose"));
  factory.registerNodeType<FromLL>("FromLL", with_default("fromLL"));
  factory.registerNodeType<ReceiveRoute>("ReceiveRoute",
                                         with_default("waypoints"));
  factory.registerNodeType<MakePose>("MakePose");
  factory.registerNodeType<SelectWaypoint>("SelectWaypoint");
}
