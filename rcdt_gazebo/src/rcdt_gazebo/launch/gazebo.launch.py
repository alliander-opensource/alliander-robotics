# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.substitutions import PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare
import os


def generate_launch_description() -> LaunchDescription:
    """Generate the launch description for the Panther robot.

    Returns:
        LaunchDescription: The launch description for the Panther robot.
    """

    world_file = os.environ.get("WORLD_FILE", default="walls.sdf")
    platforms = os.environ.get("PLATFORMS", default="")

    platforms = platforms.replace(" ", "").split(",")

    gazebo_launch = IncludeLaunchDescription(
        PathJoinSubstitution(
            [FindPackageShare("rcdt_gazebo"), "launch", "gazebo_robot.launch.py"]
        ),
        launch_arguments={
            "load_gazebo_ui": "True",
            "world": world_file,
            "platforms": platforms,
            "positions": "0,0,0.2",
            "orientations": "0,0,90",
            "parents": "none",
            "parent_links": "none",
            "bridge_topics": "",
        }.items(),
    )

    return LaunchDescription([gazebo_launch])
