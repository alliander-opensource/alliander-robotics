# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

from alliander_utilities.config_objects import Camera
from alliander_utilities.launch_argument import LaunchArgument
from alliander_utilities.launch_utils import SKIP, state_publisher_node, static_tf_node
from alliander_utilities.register import Register, RegisteredLaunchDescription
from alliander_utilities.ros_utils import get_file_path
from launch import LaunchContext, LaunchDescription
from launch.actions import OpaqueFunction

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
        platform="seekthermal",
        xacro="seekthermal.urdf.xacro",
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
        get_file_path("alliander_seekthermal", ["launch"], "hardware.launch.py"),
        {"platform_config": camera_config.to_str()},
    )

    return [
        Register.on_start(state_publisher, context),
        Register.on_start(static_tf, context),
        Register.group(hardware, context) if not camera_config.simulation else SKIP,
    ]


def generate_launch_description() -> LaunchDescription:
    """Generate the launch description for the Panther robot.

    Returns:
        LaunchDescription: The launch description for the Panther robot.
    """
    return LaunchDescription(
        [
            platform_arg.declaration,
            OpaqueFunction(function=launch_setup),
        ]
    )
