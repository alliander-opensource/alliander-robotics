// # SPDX-FileCopyrightText: Alliander N. V.
//
// # SPDX-License-Identifier: Apache-2.0

#include <alliander_behavior/behaviors/common/call_trigger_action.hpp>
#include <alliander_behavior/behaviors/common/publish_status.hpp>
#include <alliander_behavior/behaviors/common/trigger_received.hpp>
#include <behaviortree_ros2/plugins.hpp>

BT_REGISTER_ROS_NODES(factory, params) {
  using namespace alliander_behavior;

  factory.registerNodeType<CallTriggerAction>("CallTriggerAction", params);
  factory.registerNodeType<TriggerReceived>("TriggerReceived", params);

  auto status = params;
  status.default_port_value = "status";
  factory.registerNodeType<PublishStatus>("PublishStatus", status);
}
