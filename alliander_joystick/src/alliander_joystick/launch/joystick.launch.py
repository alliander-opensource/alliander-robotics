# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

import warnings

from alliander_utilities.config_objects import PlatformList
from alliander_utilities.launch_argument import LaunchArgument
from alliander_utilities.register import Register
from launch import LaunchContext, LaunchDescription
from launch.actions import OpaqueFunction
from launch_ros.actions import Node

platform_list_arg = LaunchArgument("platform_list", "")


def launch_setup(context: LaunchContext) -> list:
    """The launch setup.

    Args:
        context (LaunchContext): The launch context.

    Returns:
        list: The actions to start.

    Raises:
        RuntimeError: No arm nor vehicle platform is found.
    """
    platforms = PlatformList.from_str(platform_list_arg.string_value(context)).platforms

    # Create default namespaces which can be ignored when left unchanged
    arm_namespace = "/arm"
    vehicle_namespace = "/vehicle"

    # Find arm / vehicle platforms in the platform list
    for platform in platforms:
        match platform.platform_type:
            case "Arm":
                if arm_namespace == "/arm":
                    arm_namespace = f"/{platform.namespace}"
                else:
                    warnings.warn(
                        "No support for multiple arms yet, only accepting the first arm.",
                        RuntimeWarning,
                        stacklevel=1,
                    )

            case "Vehicle":
                if vehicle_namespace == "/vehicle":
                    vehicle_namespace = f"/{platform.namespace}"
                else:
                    warnings.warn(
                        "No support for multiple vehicles yet, only accepting the first vehicle.",
                        RuntimeWarning,
                        stacklevel=1,
                    )

            case _:
                pass

    if arm_namespace == "/arm" and vehicle_namespace == "/vehicle":
        raise RuntimeError(
            "No arm/vehicle platform present, cancelling the joystick manager."
        )

    joystick_manager = Node(
        package="alliander_joystick",
        executable="joystick_manager",
        name="joystick_manager",
        parameters=[
            {"arm_cmd_topic": f"{arm_namespace}/servo_node/delta_twist_cmds"},
            {"arm_frame_id": f"{arm_namespace[1:]}/base_link"},
            {"arm_gripper_name": f"{arm_namespace}/gripper"},
            {
                "arm_home_service": f"{arm_namespace}/moveit_manager/move_to_configuration"
            },
            {"arm_pause_servo_service": f"{arm_namespace}/servo_node/pause_servo"},
            {"vehicle_cmd_topic": f"{vehicle_namespace}/cmd_vel"},
            {"vehicle_estop_reset": f"{vehicle_namespace}/hardware/e_stop_reset"},
            {"vehicle_estop_trigger": f"{vehicle_namespace}/hardware/e_stop_trigger"},
        ],
    )

    joystick_controller = Node(
        package="joy",
        executable="game_controller_node",
        parameters=[
            {"sticky_buttons": True},
        ],
    )

    return [
        Register.on_start(joystick_controller, context),
        Register.on_start(joystick_manager, context),
    ]


def generate_launch_description() -> LaunchDescription:
    """Generate the launch description.

    Returns:
        LaunchDescription: The launch description.
    """
    return LaunchDescription(
        [
            platform_list_arg.declaration,
            OpaqueFunction(function=launch_setup),
        ]
    )
