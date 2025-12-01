# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

from launch import LaunchDescription
from rcdt_tools.rviz import Rviz
from rcdt_tools.vizanti import Vizanti
import os


def add_arm(namespace: str, use_moveit: bool):
    if use_moveit:
        Rviz.moveit_namespaces.append(namespace)
        Rviz.add_motion_planning_plugin(namespace)
        Rviz.add_planning_scene(namespace)
        Rviz.add_robot_state(namespace)
        Rviz.add_trajectory(namespace)


def generate_launch_description() -> LaunchDescription:
    """Generate the launch description for the Panther robot.

    Returns:
        LaunchDescription: The launch description for the Panther robot.
    """

    use_rviz = os.environ.get("USE_RVIZ", default="false").lower() == True
    use_vizanti = os.environ.get("USE_VIZANTI", default="false").lower() == True
    use_moveit = os.environ.get("USE_MOVEIT", default="false").lower() == True
    platforms = os.environ.get("PLATFORMS", default="")

    platforms = platforms.replace(" ", "").split(",")

    for platform in platforms:
        match platform.lower():
            case "franka": 
                add_arm("franka1", use_moveit)


    nodes = []

    if use_rviz:
        pass
    if use_vizanti:
        pass

    return LaunchDescription(
        [nodes]
    )
