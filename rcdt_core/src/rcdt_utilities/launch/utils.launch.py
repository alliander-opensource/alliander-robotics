# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

from launch import LaunchContext, LaunchDescription
from launch.actions import OpaqueFunction
from launch_ros.actions import Node
from rcdt_utilities.register import Register


def launch_setup(context: LaunchContext) -> list:
    """Launches the utilities launch file.

    Args:
        context (LaunchContext): The launch context.

    Returns:
        list: A list of actions to be executed in the launch description.
    """
    manipulate_pose = Node(package="rcdt_utilities", executable="manipulate_pose")

    return [
        Register.on_start(manipulate_pose, context),
    ]


def generate_launch_description() -> LaunchDescription:
    """Launches the utilities launch file.

    Returns:
        LaunchDescription: The launch description for the utilities launch file.
    """
    return LaunchDescription([OpaqueFunction(function=launch_setup)])
