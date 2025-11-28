# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

import os.path

from launch import LaunchContext, LaunchDescription
from launch.actions import OpaqueFunction
from launch_ros.actions import Node
from rcdt_launch.moveit import Moveit
from rcdt_launch.rviz import Rviz
from rcdt_utilities.register import Register


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

    if any(
        [
            Rviz.load_motion_planning_plugin,
            Rviz.load_planning_scene,
            Rviz.load_robot_state,
            Rviz.load_trajectory,
        ]
    ):
        for namespace in Rviz.moveit_namespaces:
            configuration = Moveit.configurations[namespace]

            parameters.extend(
                [
                    {
                        f"{namespace}_robot_description": configuration.robot_description[
                            "robot_description"
                        ]
                    },
                    {
                        f"{namespace}_robot_description_semantic": configuration.robot_description_semantic[
                            "robot_description_semantic"
                        ]
                    },
                    {
                        f"{namespace}_robot_description_kinematics": configuration.robot_description_kinematics[
                            "robot_description_kinematics"
                        ]
                    },
                    configuration.planning_pipelines,
                    configuration.pilz_cartesian_limits,
                ]
            )

    rviz = Node(
        package="rviz2",
        executable="rviz2",
        arguments=arguments,
        parameters=parameters,
        remappings=remappings,
    )

    return [
        Register.on_log(rviz, "OpenGl version:", context),
    ]


def generate_launch_description() -> LaunchDescription:
    """Generate the launch description for RViz.

    Returns:
        LaunchDescription: The launch description for RViz.
    """
    return LaunchDescription([OpaqueFunction(function=launch_setup)])
