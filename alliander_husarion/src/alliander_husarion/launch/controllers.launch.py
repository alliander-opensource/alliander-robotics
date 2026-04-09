# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

from alliander_utilities.config_objects import Vehicle
from alliander_utilities.launch_argument import LaunchArgument
from alliander_utilities.register import Register
from launch import LaunchContext, LaunchDescription
from launch.actions import OpaqueFunction
from launch_ros.actions import Node

platform_arg = LaunchArgument("platform_config", "")

TIMEOUT = 100


def launch_setup(context: LaunchContext) -> list:
    """Setup the launch description for the Panther controllers.

    Args:
        context (LaunchContext): The launch context.

    Returns:
        list: A list of actions to be executed in the launch description.
    """
    vehicle_config = Vehicle.from_str(platform_arg.string_value(context))

    twist_mux = Node(
        package="twist_mux",
        executable="twist_mux",
        name="twist_mux",
        namespace=vehicle_config.namespace,
        parameters=[
            {"use_stamped": True},
            {
                "topics": {
                    "navigation": {
                        "topic": "cmd_vel_nav",
                        "timeout": 0.5,
                        "priority": 10,
                    },
                    "joystick": {
                        "topic": "cmd_vel_joy",
                        "timeout": 0.5,
                        "priority": 100,
                    },
                }
            },
        ],
        remappings=[("cmd_vel_out", "cmd_vel_test")],
    )

    joint_state_broadcaster_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=[
            "joint_state_broadcaster",
            "--switch-timeout",
            str(TIMEOUT),
            "--controller-ros-args",
            "--remap joint_state_broadcaster/transition_event:=joint_state_broadcaster/_transition_event",
        ],
        name="joint_state_broadcaster",
        namespace=vehicle_config.namespace,
    )

    imu_broadcaster_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=[
            "imu_broadcaster",
            "--switch-timeout",
            str(TIMEOUT),
            "--controller-ros-args",
            f"--ros-args -p sensor_name:={vehicle_config.namespace}/imu",
            "--controller-ros-args",
            f"--ros-args -p frame_id:={vehicle_config.namespace}/imu_link",
            "--controller-ros-args",
            "--remap imu_broadcaster/imu:=imu/data",
            "--controller-ros-args",
            "--remap imu_broadcaster/transition_event:=imu_broadcaster/_transition_event",
        ],
        name="imu_broadcaster",
        namespace=vehicle_config.namespace,
    )

    drive_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=[
            "drive_controller",
            "--switch-timeout",
            str(TIMEOUT),
            "--controller-manager",
            "controller_manager",
            "--controller-ros-args",
            "--remap drive_controller/cmd_vel:=cmd_vel_test",
            "--controller-ros-args",
            "--remap drive_controller/odom:=odometry/wheels",
            "--controller-ros-args",
            "--remap drive_controller/transition_event:=drive_controller/_transition_event",
        ],
        name="drive_controller",
        namespace=vehicle_config.namespace,
    )

    return [
        Register.on_start(twist_mux, context),
        Register.on_exit(joint_state_broadcaster_spawner, context),
        Register.on_exit(imu_broadcaster_spawner, context),
        Register.on_exit(drive_controller_spawner, context),
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
