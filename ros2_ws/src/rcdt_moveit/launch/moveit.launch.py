# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

from launch import LaunchContext, LaunchDescription
from launch.actions import ExecuteProcess, OpaqueFunction
from launch_ros.actions import Node
from rcdt_launch.moveit import Moveit
from rcdt_utilities.launch_argument import LaunchArgument
from rcdt_utilities.register import Register

namespace_arm_arg = LaunchArgument("namespace_arm", "")
namespace_camera_arg = LaunchArgument("namespace_camera", "")


def launch_setup(context: LaunchContext) -> list:
    """Setup the launch description for MoveIt with Servo.

    Args:
        context (LaunchContext): The launch context.

    Returns:
        list: A list of actions to be executed in the launch description.
    """
    namespace_arm = namespace_arm_arg.string_value(context)
    namespace_camera = namespace_camera_arg.string_value(context)
    configuration = Moveit.configurations[namespace_arm]

    # Parameters required for move_group:
    move_group_parameters = []
    move_group_parameters.append(configuration.robot_description)
    move_group_parameters.append(configuration.robot_description_semantic)
    move_group_parameters.append(configuration.robot_description_kinematics)
    move_group_parameters.append(configuration.joint_limits)
    move_group_parameters.append(configuration.trajectory_execution)
    move_group_parameters.append(configuration.planning_pipelines)
    move_group_parameters.append(configuration.pilz_cartesian_limits)
    move_group_parameters.append(configuration.sensors_3d)
    move_group_parameters.append({"octomap_resolution": 0.02})

    # Parameters required for moveit_manager:
    moveit_manager_parameters = []
    moveit_manager_parameters.append(configuration.robot_description)
    moveit_manager_parameters.append(configuration.robot_description_semantic)
    moveit_manager_parameters.append(configuration.robot_description_kinematics)
    moveit_manager_parameters.append({"namespace_camera": namespace_camera})

    # Parameters required for moveit_servo:
    moveit_servo_parameters = []
    moveit_servo_parameters.append(configuration.robot_description)
    moveit_servo_parameters.append(configuration.robot_description_semantic)
    moveit_servo_parameters.append(configuration.robot_description_kinematics)
    moveit_servo_parameters.append(Moveit.servo_configurations[namespace_arm])

    move_group = Node(
        package="moveit_ros_move_group",
        executable="move_group",
        parameters=move_group_parameters,
        namespace=namespace_arm,
    )

    moveit_manager = Node(
        package="rcdt_moveit",
        executable="moveit_manager",
        output="screen",
        parameters=moveit_manager_parameters,
        namespace=namespace_arm,
    )

    moveit_servo = Node(
        package="moveit_servo",
        executable="servo_node",
        parameters=moveit_servo_parameters,
        namespace=namespace_arm,
    )

    switch_servo_type_to_twist = ExecuteProcess(
        cmd=[
            "ros2",
            "service",
            "call",
            f"/{namespace_arm}/servo_node/switch_command_type",
            "moveit_msgs/srv/ServoCommandType",
            "{command_type: 1}",
        ]
    )

    return [
        Register.on_log(
            move_group, "MoveGroup context initialization complete", context
        ),
        Register.on_log(
            moveit_manager, "Ready to take commands for planning group", context
        ),
        Register.on_log(moveit_servo, "Servo initialized successfully", context),
        Register.on_exit(switch_servo_type_to_twist, context),
    ]


def generate_launch_description() -> LaunchDescription:
    """Generate the launch description for MoveIt with Servo.

    Returns:
        LaunchDescription: The launch description containing the actions to be executed.
    """
    return LaunchDescription(
        [
            namespace_arm_arg.declaration,
            namespace_camera_arg.declaration,
            OpaqueFunction(function=launch_setup),
        ]
    )
