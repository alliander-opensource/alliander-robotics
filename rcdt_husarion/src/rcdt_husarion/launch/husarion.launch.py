# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

import os

from launch import LaunchContext, LaunchDescription
from launch.actions import OpaqueFunction
from rcdt_husarion.vehicle import Vehicle
from rcdt_utilities import launch_utils
from rcdt_utilities.register import Register, RegisteredLaunchDescription
from rcdt_utilities.ros_utils import get_file_path


def launch_setup(context: LaunchContext) -> list:
    """Generate the launch description for the navigation stack.

    Returns:
        LaunchDescription: The launch description containing the actions to be executed.
    """
    simulation = os.environ.get("SIMULATION", default="False").lower() == "true"

    description = RegisteredLaunchDescription(
        get_file_path("rcdt_husarion", ["launch"], "description.launch.py")
    )

    controllers = RegisteredLaunchDescription(
        get_file_path("rcdt_husarion", ["launch"], "controllers.launch.py")
    )

    vehicle = Vehicle("panther", simulation=simulation)
    map_link = vehicle.create_map_link()

    return [
        Register.group(description, context) if simulation else launch_utils.SKIP,
        Register.on_start(map_link, context),
        Register.group(controllers, context) if simulation else launch_utils.SKIP,
    ]


def generate_launch_description() -> LaunchDescription:
    """Generate the launch description for the Panther robot.

    Returns:
        LaunchDescription: The launch description for the Panther robot.
    """
    return LaunchDescription(
        [
            OpaqueFunction(function=launch_setup),
        ]
    )
