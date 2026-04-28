# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0
from alliander_utilities.config_objects import ThermalCamera
from alliander_utilities.launch_argument import LaunchArgument
from alliander_utilities.register import Register
from launch import LaunchContext, LaunchDescription
from launch.actions import OpaqueFunction
from launch_ros.actions import Node

platform_arg = LaunchArgument("platform_config", "")


def launch_setup(context: LaunchContext) -> list:
    """The launch setup.

    Args:
        context (LaunchContext): The launch context.

    Returns:
        list: The actions to start.
    """
    camera_config = ThermalCamera.from_str(platform_arg.string_value(context))

    seekthermal_bridge_node = Node(
        package="alliander_seekthermal",
        executable="alliander_seekthermal.py",
        output="both",
        parameters=[
            {
                "frame_id": f"/{camera_config.namespace}/seekthermal_link_optical",
            }
        ],
        remappings=[
            (
                "/topic_out_image/compressed",
                "thermal/image/compressed",
            )
        ],
        namespace=camera_config.namespace,
    )

    return [
        Register.on_start(seekthermal_bridge_node, context),
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
