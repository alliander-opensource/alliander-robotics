# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0
from alliander_utilities.config_objects import PlatformList, VisualizationConfig
from alliander_utilities.launch_argument import LaunchArgument
from alliander_utilities.launch_utils import SKIP
from alliander_utilities.register import Register, RegisteredLaunchDescription
from alliander_utilities.ros_utils import get_file_path
from alliander_visualization.tool_manager import ApplyConfigurations, Foxglove
from launch import LaunchContext, LaunchDescription
from launch.actions import OpaqueFunction
from launch_ros.actions import Node, SetParameter

config_arg = LaunchArgument("vis_config", "")
platform_list_arg = LaunchArgument("platform_list", "")


def launch_setup(context: LaunchContext) -> list:
    """The launch setup.

    Args:
        context (LaunchContext): The launch context.

    Returns:
        list: The actions to start.
    """
    config = VisualizationConfig.from_str(config_arg.string_value(context))
    platforms = PlatformList.from_str(platform_list_arg.string_value(context))

    ApplyConfigurations(config, platforms)
    simulation = all(platform.simulation for platform in platforms.platforms)

    rviz = RegisteredLaunchDescription(
        get_file_path("alliander_visualization", ["launch"], "rviz.launch.py")
    )

    vizanti = RegisteredLaunchDescription(
        get_file_path("alliander_visualization", ["launch"], "vizanti.launch.py")
    )

    gui = Node(
        package="alliander_visualization",
        executable="alliander_gui.py",
        parameters=[{"platform_list": platforms.to_str()}],
    )

    foxglove = Node(
        package="foxglove_bridge",
        executable="foxglove_bridge",
        parameters=[
            {
                "topic_whitelist": Foxglove.topics,
                "service_whitelist": Foxglove.services,
                "param_whitelist": [""],
                "client_topic_whitelist": [""],
            }
        ],
    )

    return [
        SetParameter(name="use_sim_time", value=simulation),
        Register.group(rviz, context) if config.rviz else SKIP,
        Register.group(vizanti, context) if config.vizanti else SKIP,
        Register.on_start(gui, context) if config.gui else SKIP,
        Register.on_start(foxglove, context),
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
