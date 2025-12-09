# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

import os

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from rcdt_utilities.ros_utils import get_file_path


def generate_launch_description() -> LaunchDescription:
    """Generate the launch description for the navigation stack.

    Returns:
        LaunchDescription: The launch description containing the actions to be executed.
    """
    simulation = os.environ.get("SIMULATION", default="False").lower() == "true"

    nodes = []

    controller = IncludeLaunchDescription(
        get_file_path("rcdt_franka", ["launch"], "controllers.launch.py")
    )
    nodes.append(controller)

    if simulation:
        description = IncludeLaunchDescription(
            get_file_path("rcdt_franka", ["launch"], "description.launch.py")
        )
        nodes.append(description)

    return LaunchDescription(nodes)
