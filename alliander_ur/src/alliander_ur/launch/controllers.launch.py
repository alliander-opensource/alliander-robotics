# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

from alliander_utilities.config_objects import Arm
from alliander_utilities.launch_argument import LaunchArgument
from alliander_utilities.register import Register
from launch import LaunchContext, LaunchDescription
from launch.actions import OpaqueFunction
from launch_ros.actions import Node

TIMEOUT = 100

platform_arg = LaunchArgument("platform_config", "")


def launch_setup(context: LaunchContext) -> list:
    """Setup the launch description for the UR controllers.

    Args:
        context (LaunchContext): The launch context.

    Returns:
        list: A list of actions to be executed in the launch description.
    """
    arm_config = Arm.from_str(platform_arg.string_value(context))

    joint_state_broadcaster_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=[
            "joint_state_broadcaster",
            "--switch-timeout",
            str(TIMEOUT),
        ],
        namespace=arm_config.namespace,
    )

    ur5_arm_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=[
            "joint_trajectory_controller",
            "--switch-timeout",
            str(TIMEOUT),
        ],
        namespace=arm_config.namespace,
    )

    return [
        Register.on_exit(joint_state_broadcaster_spawner, context),
        Register.on_exit(ur5_arm_controller_spawner, context),
    ]


def generate_launch_description() -> LaunchDescription:
    """Generate the launch description for the UR controllers.

    Returns:
        LaunchDescription: The launch description containing the nodes and actions.
    """
    return LaunchDescription(
        [
            platform_arg.declaration,
            OpaqueFunction(function=launch_setup),
        ]
    )
