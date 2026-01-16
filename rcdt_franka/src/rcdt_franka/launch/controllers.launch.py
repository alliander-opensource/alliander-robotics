# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

from launch import LaunchContext, LaunchDescription
from launch.actions import OpaqueFunction
from launch_ros.actions import Node
from rcdt_utilities.config_objects import Arm
from rcdt_utilities.launch_argument import LaunchArgument
from rcdt_utilities.launch_utils import SKIP
from rcdt_utilities.register import Register
from rcdt_utilities.ros_utils import get_file_path

TIMEOUT = 100

platform_arg = LaunchArgument("platform_config", "")


def launch_setup(context: LaunchContext) -> list:
    """Setup the launch description for the Franka controllers.

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

    fr3_arm_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=[
            "fr3_arm_controller",
            "--switch-timeout",
            str(TIMEOUT),
        ],
        namespace=arm_config.namespace,
    )

    if arm_config.simulation:
        fr3_gripper = Node(
            package="rcdt_franka",
            executable="fr3_gripper_simulation",
            output="screen",
            namespace=arm_config.namespace,
        )
    else:
        fr3_gripper = Node(
            package="franka_gripper",
            executable="franka_gripper_node",
            name="fr3_gripper",
            parameters=[
                {
                    "robot_ip": arm_config.ip_address,
                    "joint_names": ["fr3_finger_joint1", "fr3_finger_joint2"],
                },
                get_file_path("franka_gripper", ["config"], "franka_gripper_node.yaml"),
            ],
            namespace=arm_config.namespace,
        )

    gripper_action_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["gripper_action_controller"],
        namespace=arm_config.namespace,
    )

    return [
        Register.on_exit(joint_state_broadcaster_spawner, context),
        Register.on_exit(fr3_arm_controller_spawner, context),
        Register.on_start(fr3_gripper, context),
        (
            Register.on_exit(gripper_action_controller_spawner, context)
            if arm_config.simulation
            else SKIP
        ),
    ]


def generate_launch_description() -> LaunchDescription:
    """Generate the launch description for the Franka controllers.

    Returns:
        LaunchDescription: The launch description containing the nodes and actions.
    """
    return LaunchDescription(
        [
            platform_arg.declaration,
            OpaqueFunction(function=launch_setup),
        ]
    )
