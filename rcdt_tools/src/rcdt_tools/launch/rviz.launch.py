# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

import os.path

from launch import LaunchContext, LaunchDescription
from launch.actions import OpaqueFunction
from launch_ros.actions import Node


def launch_setup(context: LaunchContext) -> list:
    """Setup the launch description for RViz.

    Args:
        context (LaunchContext): The launch context.

    Returns:
        list: A list of actions to be executed in the launch description.
    """
    arguments = []
    parameters = []
    remappings = []

    file_name = "/tmp/rviz.rviz"
    if os.path.isfile(file_name):
        arguments.extend(["--display-config", file_name])

    rviz = Node(
        package="rviz2",
        executable="rviz2",
        arguments=arguments,
        parameters=parameters,
        remappings=remappings,
    )

    return [
        # Register.on_log(rviz, "OpenGl version:", context),
        rviz
    ]


def generate_launch_description() -> LaunchDescription:
    """Generate the launch description for RViz.

    Returns:
        LaunchDescription: The launch description for RViz.
    """
    return LaunchDescription([OpaqueFunction(function=launch_setup)])
