# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

from launch import LaunchContext, LaunchDescription
from launch.actions import OpaqueFunction
from launch_ros.actions import SetParameter
from rcdt_utilities import launch_utils
from rcdt_utilities.config_objects import (
    VisualizationConfig,
)
from rcdt_utilities.launch_argument import LaunchArgument
from rcdt_utilities.register import Register, RegisteredLaunchDescription
from rcdt_utilities.ros_utils import get_file_path
from rcdt_visualization.tool_manager import ApplyConfigurations

config_arg = LaunchArgument("config", "")


def launch_setup(context: LaunchContext) -> list:
    """The launch setup.

    Args:
        context (LaunchContext): The launch context.

    Returns:
        list: The actions to start.
    """
    config = VisualizationConfig.from_str(config_arg.string_value(context))
    ApplyConfigurations(config)
    simulation = all(platform.simulation for platform in config.platforms)

    rviz = RegisteredLaunchDescription(
        get_file_path("rcdt_visualization", ["launch"], "rviz.launch.py")
    )

    vizanti = RegisteredLaunchDescription(
        get_file_path("rcdt_visualization", ["launch"], "vizanti.launch.py")
    )

    return [
        SetParameter(name="use_sim_time", value=simulation),
        Register.group(rviz, context) if config.rviz else launch_utils.SKIP,
        Register.group(vizanti, context) if config.vizanti else launch_utils.SKIP,
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
