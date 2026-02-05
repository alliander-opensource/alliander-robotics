# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

# This should become the gist of the launch file but I can't seem to get it to work yet with the parameters.

from launch import LaunchContext, LaunchDescription
from launch.actions import OpaqueFunction
from launch_ros.actions import Node
from rcdt_utilities.config_objects import Joystick
from rcdt_utilities.launch_argument import LaunchArgument
from rcdt_utilities.register import Register

platform_arg = LaunchArgument("platform_config", "")


def launch_setup(context: LaunchContext) -> list:
    """The launch setup.

    Args:
        context (LaunchContext): The launch context.

    Returns:
        list: The actions to start.
    """
    joystick_config = Joystick.from_str(platform_arg.string_value(context))

    joystick_manager = Node(
        package="rcdt_joystick",
        executable="joystick_manager",
        name="joystick_manager",
        parameters=[
            {"arm_cmd_topic": joystick_config.arm_cmd_topic},
            {"arm_frame_id": joystick_config.arm_frame_id},
            {"arm_gripper_name": joystick_config.arm_gripper_name},
            {"arm_home_service": joystick_config.arm_home_service},
            {"vehicle_cmd_topic": joystick_config.vehicle_cmd_topic},
            {"vehicle_estop_reset": joystick_config.vehicle_estop_reset},
            {"vehicle_estop_trigger": joystick_config.vehicle_estop_trigger},
        ]
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
            platform_arg.declaration,
            OpaqueFunction(function=launch_setup),
        ]
    )
