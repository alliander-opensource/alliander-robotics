#!/usr/bin/env python3

# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

from dataclasses import dataclass

import rclpy
import rclpy.client
from rcdt_utilities.ros_utils import spin_node
from rclpy.node import Node, Publisher
from rclpy.qos import QoSDurabilityPolicy, QoSHistoryPolicy, QoSProfile
from sensor_msgs.msg import Joy
from std_msgs.msg import String
from std_srvs.srv import Trigger

# Define the latched QoS profile
latched_qos = QoSProfile(
    depth=1,
    durability=QoSDurabilityPolicy.TRANSIENT_LOCAL,
    history=QoSHistoryPolicy.KEEP_LAST,
)


@dataclass
class Output:
    """Data class representing a joystick output configuration.

    Attributes:
        button (int): The index of the joystick button to monitor.
        topic (str | None): The topic to publish the Joy message to when the button state changes.
        service (str | None): The service to call when the button state changes.
        state (int): The current state of the button (pressed or not).
    """

    button: int
    topic: str | None = None
    service: str | None = None
    state: int = 0

    def state_changed(self, state: bool) -> bool:
        """Check if the state of the button has changed.

        Args:
            state (bool): The current state of the button (pressed or not).

        Returns:
            bool: True if the state has changed, False otherwise.
        """
        if self.state == state:
            return False
        self.state = state
        return True


class JoyTopicManager(Node):
    """A ROS2 node that manages joystick topics based on button presses.

    A button can be configured to either switch the topic to which Joy messages are published,
    or to call a service.
    """

    def __init__(self) -> None:
        """Initialize the JoyTopicManager node."""
        super().__init__("joy_topic_manager")
        self.declare_parameter("joy_topic", value="/joy")
        self.declare_parameter("buttons", [0])
        self.declare_parameter("services", [False])
        self.declare_parameter("topics", [""])

        joy_input = self.get_parameter("joy_topic").get_parameter_value().string_value
        buttons = (
            self.get_parameter("buttons").get_parameter_value().integer_array_value
        )
        services = self.get_parameter("services").get_parameter_value().bool_array_value
        topics = self.get_parameter("topics").get_parameter_value().string_array_value

        if not (len(buttons) == len(services) == len(topics)):
            self.get_logger().error(
                "Parameters 'buttons', 'services', and 'topic' must have the same length."
            )
            return

        self.outputs: list[Output] = []
        for i in range(len(buttons)):
            output = Output(buttons[i])
            if services[i]:
                output.service = topics[i]
            else:
                output.topic = topics[i]
            self.outputs.append(output)

        self.pubs: dict[str, Publisher] = {}
        self.srvs: dict[str, rclpy.client.Client] = {}
        for output in self.outputs:
            if output.topic not in {None, ""}:
                self.pubs[output.topic] = self.create_publisher(Joy, output.topic, 10)
            if output.service is not None:
                self.srvs[output.service] = self.create_client(Trigger, output.service)

        self.topic = ""
        self.create_subscription(Joy, joy_input, self.handle_joy_message, 10)
        self.state_pub = self.create_publisher(
            String, "~/state", qos_profile=latched_qos
        )

    def handle_joy_message(self, msg: Joy) -> None:
        """Handle incoming Joy messages and apply output changes based on button states.

        Args:
            msg (Joy): The incoming Joy message containing button states.
        """
        self.apply_output_changes(msg)
        self.pass_joy_message(msg)

    def apply_output_changes(self, msg: Joy) -> None:
        """Apply changes to the output topics based on the current Joy message.

        Args:
            msg (Joy): The incoming Joy message containing button states.
        """
        for output in self.outputs:
            if output.button >= len(msg.buttons):
                self.get_logger().warn(
                    f"Button index {output.button} out of range in Joy message with {len(msg.buttons)} buttons."
                )
                continue
            state = msg.buttons[output.button]
            if output.state_changed(state):
                if output.topic is not None:
                    self.change_topic(output.topic)
                elif output.service is not None:
                    self.call_service(output.service)

    def call_service(self, service: str) -> None:
        """Call a ROS2 service..

        Args:
            service (str): The service to call.
        """
        if self.srvs[service].wait_for_service(timeout_sec=1.0):
            self.get_logger().info(f"Calling {service}.")
            self.srvs[service].call_async(Trigger.Request())
        else:
            self.get_logger().error(f"Service {service} not available, cannot call.")

    def change_topic(self, topic: str) -> None:
        """Change the currently active topic and publish the new state.

        Args:
            topic (str): The new topic to which Joy messages should be published.
        """
        if self.topic == topic:
            return
        self.topic = topic

        msg = String()
        msg.data = self.topic
        self.state_pub.publish(msg)

        if not self.topic:
            self.get_logger().info("Joy topic passing stopped.")
        else:
            self.get_logger().info(f"Joy topic is now passed to {self.topic}.")

    def pass_joy_message(self, msg: Joy) -> None:
        """Pass the Joy message to the currently active topic.

        Args:
            msg (Joy): The Joy message to be published.
        """
        if not self.topic:
            return
        pub = self.pubs[self.topic]
        pub.publish(msg)


def main(args: list | None = None) -> None:
    """Main function to initialize the JoyTopicManager node and start spinning it.

    Args:
        args (list | None): Command line arguments, defaults to None.
    """
    rclpy.init(args=args)
    node = JoyTopicManager()
    spin_node(node)


if __name__ == "__main__":
    main()
