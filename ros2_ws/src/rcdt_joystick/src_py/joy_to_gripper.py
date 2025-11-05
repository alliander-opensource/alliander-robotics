#!/usr/bin/env python3

# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

from threading import Thread
from typing import Literal

import rclpy
from rcdt_messages.action import Trigger as TriggerAction
from rcdt_utilities.launch_utils import get_file_path, get_yaml, spin_executor
from rclpy.action import ActionClient
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node
from sensor_msgs.msg import Joy


class JoyToGripper(Node):
    """A ROS2 node that maps joystick button presses to gripper actions.

    This node subscribes to joystick input and calls the appropriate service
    to open or close the gripper based on button presses.
    """

    def __init__(self):
        """A ROS2 node that maps joystick button presses to gripper actions."""
        super().__init__("joy_to_gripper")

        self.declare_parameter("config_pkg", "")
        config_pkg = self.get_parameter("config_pkg").get_parameter_value().string_value

        ns = self.get_namespace()
        self.open_gripper = ActionClient(self, TriggerAction, f"{ns}/gripper/open")
        self.close_gripper = ActionClient(self, TriggerAction, f"{ns}/gripper/close")
        self.create_subscription(Joy, f"{ns}/joy", self.handle_input, 10)

        config = get_file_path(config_pkg, ["config"], "gamepad_mapping.yaml")
        self.mapping: dict = get_yaml(config)
        self.button_actions: dict = self.mapping.get("buttons", {})
        self.button_states = {}
        for button in self.button_actions:
            self.button_states[button] = 0

        self.busy = False

    def handle_input(self, sub_msg: Joy) -> None:
        """Handle incoming joystick messages and perform actions based on button presses.

        Args:
            sub_msg (Joy): The incoming joystick message containing button states.
        """
        for button, action in self.button_actions.items():
            if button >= len(sub_msg.buttons):
                self.get_logger().warn(
                    f"Button index {button} out of range (buttons: {len(sub_msg.buttons)})."
                )
                continue
            state = sub_msg.buttons[button]
            if state == self.button_states[button]:
                continue
            self.button_states[button] = state
            thread = Thread(target=self.perform_action_if_not_busy, args=[action])
            thread.start()

    def perform_action_if_not_busy(
        self, action: Literal["open_gripper", "close_gripper"]
    ) -> None:
        """Perform the specified action if the node is not busy.

        Args:
            action (Literal["open_gripper", "close_gripper"]): The action to perform.
        """
        if self.busy:
            return
        self.busy = True
        match action:
            case "open_gripper":
                self.open_gripper.send_goal_async(TriggerAction.Goal())
            case "close_gripper":
                self.close_gripper.send_goal_async(TriggerAction.Goal())
        self.busy = False


def main(args: list | None = None) -> None:
    """Main function to initialize the ROS 2 node and start the executor.

    Args:
        args (list | None): Command line arguments, defaults to None.
    """
    rclpy.init(args=args)
    executor = MultiThreadedExecutor()
    node = JoyToGripper()
    executor.add_node(node)
    spin_executor(executor)


if __name__ == "__main__":
    main()
