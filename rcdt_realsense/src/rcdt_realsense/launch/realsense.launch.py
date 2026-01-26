# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

from launch import LaunchContext, LaunchDescription
from launch.actions import OpaqueFunction
from launch_ros.actions import Node
from rcdt_utilities.config_objects import Camera
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
    camera_config = Camera.from_str(platform_arg.string_value(context))

    state_publisher = state_publisher_node(
        namespace=camera_config.namespace,
        platform="realsense",
        xacro="rcdt_realsense_d435.urdf.xacro",
        xacro_arguments={
            "parent": "" if camera_config.parent.link else "world",
        },
    )

    parent = camera_config.parent
    static_tf = static_tf_node(
        parent_frame=f"{parent.namespace}/{parent.link}" if parent.link else "map",
        child_frame=f"{camera_config.namespace}/{parent.connects_to}",
        position=camera_config.position,
        orientation=camera_config.orientation,
    )

    hardware = RegisteredLaunchDescription(
        get_file_path("rcdt_realsense", ["launch"], "hardware.launch.py"),
        {"namespace": camera_config.namespace},
    )

    convert_32FC1_to_16UC1 = Node(  # noqa: N806
        package="rcdt_utilities",
        executable="convert_32FC1_to_16UC1",
        namespace=camera_config.namespace,
    )

    return [
        Register.on_start(state_publisher, context),
        Register.on_start(static_tf, context),
        Register.group(hardware, context) if not camera_config.simulation else SKIP,
        Register.on_start(convert_32FC1_to_16UC1, context)
        if camera_config.simulation
        else SKIP,
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
