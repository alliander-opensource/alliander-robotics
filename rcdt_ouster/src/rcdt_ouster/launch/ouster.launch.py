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
    namespace = "ouster"

    state_publisher = state_publisher_node(
        namespace=namespace, platform="ouster", xacro="rcdt_os1_128.urdf.xacro"
    )

    map_link = static_tf_node("map", f"{namespace}/base_link")

    hardware = RegisteredLaunchDescription(
        get_file_path("rcdt_ouster", ["launch"], "hardware.launch.py"),
        {"namespace": namespace},
    )

    target_frame = ""
    pointcloud_to_laserscan_node = Node(
        package="pointcloud_to_laserscan",
        executable="pointcloud_to_laserscan_node",
        remappings=[
            ("cloud_in", f"/{namespace}/scan/points"),
            ("scan", f"/{namespace}/scan"),
        ],
        parameters=[
            {
                "target_frame": target_frame,
                "min_height": 0.1,
                "max_height": 2.0,
                "range_min": 0.05,
                "range_max": 90.0,
            }
        ],
        namespace=namespace,
    )

    return [
        Register.on_start(state_publisher, context),
        Register.on_start(map_link, context),
        Register.group(hardware, context) if not simulation else SKIP,
        Register.on_start(pointcloud_to_laserscan_node, context),
    ]


def generate_launch_description() -> LaunchDescription:
    """Generate the launch description.

    Returns:
        LaunchDescription: The launch description.
    """
    return LaunchDescription(
        [
            OpaqueFunction(function=launch_setup),
        ]
    )
