# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

from launch import LaunchContext, LaunchDescription
from launch.actions import OpaqueFunction
from launch_ros.actions import Node
from rcdt_utilities.config_objects import Lidar
from rcdt_utilities.launch_argument import LaunchArgument
from rcdt_utilities.launch_utils import SKIP, state_publisher_node, static_tf_node
from rcdt_utilities.register import Register, RegisteredLaunchDescription
from rcdt_utilities.ros_utils import get_file_path

platform_arg = LaunchArgument("platform_config", "")


def launch_setup(context: LaunchContext) -> list:
    """The launch setup.

    Args:
        context (LaunchContext): The launch context.

    Returns:
        list: The actions to start.
    """
    lidar_config = Lidar.from_str(platform_arg.string_value(context))

    state_publisher = state_publisher_node(
        namespace=lidar_config.namespace,
        platform="ouster",
        xacro="rcdt_os1_128.urdf.xacro",
        xacro_arguments={
            "parent": "" if lidar_config.parent.link else "world",
        },
    )

    parent = lidar_config.parent
    static_tf = static_tf_node(
        parent_frame=f"{parent.namespace}/{parent.link}" if parent.link else "map",
        child_frame=f"{lidar_config.namespace}/{parent.connects_to}",
        position=lidar_config.position,
        orientation=lidar_config.orientation,
    )

    hardware = RegisteredLaunchDescription(
        get_file_path("rcdt_ouster", ["launch"], "hardware.launch.py"),
        {"platform_config": lidar_config.to_str()},
    )

    target_frame = ""
    pointcloud_to_laserscan_node = Node(
        package="pointcloud_to_laserscan",
        executable="pointcloud_to_laserscan_node",
        remappings=[
            ("cloud_in", f"/{lidar_config.namespace}/scan/points"),
            ("scan", f"/{lidar_config.namespace}/scan"),
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
        namespace=lidar_config.namespace,
    )

    return [
        Register.on_start(state_publisher, context),
        Register.on_start(static_tf, context),
        Register.group(hardware, context) if not lidar_config.simulation else SKIP,
        Register.on_start(pointcloud_to_laserscan_node, context),
    ]


def generate_launch_description() -> LaunchDescription:
    """Generate the launch description.

    Returns:
        LaunchDescription: The launch description.
    """
    return LaunchDescription(
        [
            platform_arg.declaration,
            OpaqueFunction(function=launch_setup),
        ]
    )
