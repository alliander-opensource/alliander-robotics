# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

from launch import LaunchDescription
from rcdt_utilities.register import RegisteredLaunchDescription
from rcdt_utilities.launch_argument import LaunchArgument
from rcdt_utilities.ros_utils import get_file_path
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import PathJoinSubstitution
from launch_ros.actions import SetParameter
from launch_ros.substitutions import FindPackageShare
import os


def generate_launch_description() -> LaunchDescription:
    """Generate the launch description for the navigation stack.

    Returns:
        LaunchDescription: The launch description containing the actions to be executed.
    """
    simulation = os.environ.get("SIMULATION", default="False").lower() == "true"

    nodes = []

    controller = IncludeLaunchDescription(
        PathJoinSubstitution(
                [FindPackageShare("rcdt_husarion"), "launch", "controllers.launch.py"]
        ),
    )
    nodes.append(controller)

    if simulation:
        description = IncludeLaunchDescription(
            PathJoinSubstitution(
                [FindPackageShare("rcdt_husarion"), "launch", "description.launch.py"]
            ),
        )
        nodes.append(description)

    return LaunchDescription(nodes)
