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

config_arg = LaunchArgument("config", "")


def launch_setup(context: LaunchContext) -> list:
    """The launch setup.

    Args:
        context (LaunchContext): The launch context.

    Returns:
        list: The actions to start.
    """
    configuration = Lidar.from_str(config_arg.string_value(context))

    state_publisher = state_publisher_node(
        namespace=configuration.namespace,
        platform="ouster",
        xacro="rcdt_os1_128.urdf.xacro",
        xacro_arguments={
            "parent": "" if configuration.parent.link else "world",
        },
    )

    parent = configuration.parent
    static_tf = static_tf_node(
        parent_frame=f"{parent.namespace}/{parent.link}" if parent.link else "map",
        child_frame=f"{configuration.namespace}/{parent.connects_to}",
        position=configuration.position,
        orientation=configuration.orientation,
    )

    hardware = RegisteredLaunchDescription(
        get_file_path("rcdt_ouster", ["launch"], "hardware.launch.py"),
        {"namespace": configuration.namespace},
    )

    target_frame = ""
    pointcloud_to_laserscan_node = Node(
        package="pointcloud_to_laserscan",
        executable="pointcloud_to_laserscan_node",
        remappings=[
            ("cloud_in", f"/{configuration.namespace}/scan/points"),
            ("scan", f"/{configuration.namespace}/scan"),
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
        namespace=configuration.namespace,
    )

    return [
        Register.on_start(state_publisher, context),
        Register.on_start(static_tf, context),
        Register.group(hardware, context) if not configuration.simulation else SKIP,
        Register.on_start(pointcloud_to_laserscan_node, context),
    ]


def generate_launch_description() -> LaunchDescription:
    """Generate the launch description.

    Returns:
        LaunchDescription: The launch description.
    """
    return LaunchDescription(
        [
            config_arg.declaration,
            OpaqueFunction(function=launch_setup),
        ]
    )
