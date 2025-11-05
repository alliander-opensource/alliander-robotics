# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

from launch import LaunchContext, LaunchDescription
from launch.actions import OpaqueFunction
from launch_ros.actions import Node
from rcdt_utilities.launch_utils import SKIP, LaunchArgument, get_file_path
from rcdt_utilities.register import Register

namespace_arg = LaunchArgument("namespace", "franka")
simulation_arg = LaunchArgument("simulation", True, [True, False])
ip_address_arg = LaunchArgument("ip_address", "")

gripper_config = get_file_path("franka_gripper", ["config"], "franka_gripper_node.yaml")


def launch_setup(context: LaunchContext) -> list:
    """Setup the launch description for the Franka controllers.

    Args:
        context (LaunchContext): The launch context.

    Returns:
        list: A list of actions to be executed in the launch description.
    """
    namespace = namespace_arg.string_value(context)
    simulation = simulation_arg.bool_value(context)
    ip_address = ip_address_arg.string_value(context)

    joint_state_broadcaster_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_state_broadcaster"],
        namespace=namespace,
    )

    fr3_arm_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["fr3_arm_controller"],
        namespace=namespace,
    )

    if simulation:
        fr3_gripper = Node(
            package="rcdt_franka",
            executable="fr3_gripper_simulation",
            output="screen",
            namespace=namespace,
        )
    else:
        fr3_gripper = Node(
            package="franka_gripper",
            executable="franka_gripper_node",
            name="fr3_gripper",
            parameters=[
                {
                    "robot_ip": ip_address,
                    "joint_names": ["fr3_finger_joint1", "fr3_finger_joint2"],
                },
                gripper_config,
            ],
            namespace=namespace,
        )

    gripper_action_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["gripper_action_controller"],
        namespace=namespace,
    )

    return [
        Register.on_exit(joint_state_broadcaster_spawner, context),
        Register.on_exit(fr3_arm_controller_spawner, context),
        Register.on_start(fr3_gripper, context),
        (
            Register.on_exit(gripper_action_controller_spawner, context)
            if simulation
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
            simulation_arg.declaration,
            namespace_arg.declaration,
            ip_address_arg.declaration,
            OpaqueFunction(function=launch_setup),
        ]
    )
