# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

import os

from launch import LaunchContext, LaunchDescription
from launch.actions import OpaqueFunction
from launch_ros.actions import Node
from rcdt_utilities.launch_utils import SKIP, state_publisher_node, static_tf_node
from rcdt_utilities.register import Register, RegisteredLaunchDescription
from rcdt_utilities.ros_utils import get_file_path


def launch_setup(context: LaunchContext) -> list:
    """The launch setup.

    Args:
        context (LaunchContext): The launch context.

    Returns:
        list: The actions to start.
    """
    simulation = os.environ.get("SIMULATION", default="False").lower() == "true"
    namespace = "zed"

    state_publisher = state_publisher_node(
        namespace=namespace,
        platform="zed",
        xacro="rcdt_zed2i.urdf.xacro",
    )

    map_link = static_tf_node("map", f"{namespace}/base_link")

    hardware = RegisteredLaunchDescription(
        get_file_path("rcdt_zed", ["launch"], "hardware.launch.py"),
        {"namespace": namespace},
    )

    convert_32FC1_to_16UC1_node = Node(  # noqa: N806
        package="rcdt_utilities",
        executable="convert_32FC1_to_16UC1",
        namespace=namespace,
    )

    return [
        Register.on_start(state_publisher, context),
        Register.on_start(map_link, context),
        Register.on_start(hardware, context) if not simulation else SKIP,
        Register.on_start(convert_32FC1_to_16UC1_node, context) if simulation else SKIP,
    ]


def generate_launch_description() -> LaunchDescription:
    """Generate the launch description for the Panther robot.

    Returns:
        LaunchDescription: The launch description for the Panther robot.
    """
    return LaunchDescription(
        [
            OpaqueFunction(function=launch_setup),
        ]
    )
