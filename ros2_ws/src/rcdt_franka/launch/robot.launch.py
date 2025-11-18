# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

import os

from launch import LaunchContext, LaunchDescription
from launch.actions import OpaqueFunction, Shutdown
from launch_ros.actions import Node
from rcdt_utilities.launch_argument import LaunchArgument
from rcdt_utilities.launch_utils import SKIP
from rcdt_utilities.register import Register
from rcdt_utilities.ros_utils import get_file_path

namespace_arg = LaunchArgument("namespace", "")
enable_lock_unlock_arg = LaunchArgument("franka_lock_unlock", False, [True, False])
ip_address_arg = LaunchArgument("ip_address", "")


def launch_setup(context: LaunchContext) -> list:
    """Setup the launch description for the Franka robot controllers.

    Args:
        context (LaunchContext): The launch context.

    Raises:
        RuntimeError: If the required environment variables are not set.

    Returns:
        list: A list of actions to be executed in the launch description.
    """
    namespace = namespace_arg.string_value(context)
    enable_lock_unlock = enable_lock_unlock_arg.bool_value(context)
    ip_address = ip_address_arg.string_value(context)

    ns = f"/{namespace}" if namespace else ""
    hostname = ip_address
    username = os.getenv("FRANKA_USERNAME", "")
    password = os.getenv("FRANKA_PASSWORD", "")

    if (not username or not password) and enable_lock_unlock:
        raise RuntimeError(
            """You must set FRANKA_USERNAME and FRANKA_PASSWORD
            in your environment if you want to enable the Franka Lock/Unlock
            node programmatically, otherwise set franka_lock_unlock:=False ."""
        )

    franka_lock_unlock = Node(
        name="franka_lock_unlock",
        package="franka_lock_unlock",
        executable="franka_lock_unlock.py",
        output="screen",
        arguments=[hostname, username, password, "-u", "-l", "-w", "-r", "-p", "-c"],
        respawn=False,
        namespace=namespace,
    )

    franka_controllers = get_file_path("rcdt_franka", ["config"], "controllers.yaml")

    ros2_control_node = Node(
        package="controller_manager",
        executable="ros2_control_node",
        parameters=[
            franka_controllers,
            {"arm_id": "fr3"},
        ],
        remappings=[
            (f"{ns}/controller_manager/robot_description", f"{ns}/robot_description"),
            (f"{ns}/joint_states", f"{ns}/fr3_arm/joint_states"),
        ],
        namespace=namespace,
        on_exit=Shutdown(),
    )

    settings_setter = Node(
        package="rcdt_franka",
        executable="settings_setter.py",
        namespace=namespace,
    )

    joint_state_publisher = Node(
        package="joint_state_publisher",
        executable="joint_state_publisher",
        name="joint_state_publisher",
        parameters=[
            {
                "source_list": [
                    f"{ns}/fr3_arm/joint_states",
                    f"{ns}/fr3_gripper/joint_states",
                ],
                "rate": 30,
            }
        ],
        namespace=namespace,
    )

    return [
        Register.on_log(franka_lock_unlock, "Keeping persistent connection...", context)
        if enable_lock_unlock
        else SKIP,
        Register.on_start(ros2_control_node, context),
        Register.on_log(settings_setter, "Thresholds set successfully.", context),
        Register.on_start(joint_state_publisher, context),
    ]


def generate_launch_description() -> LaunchDescription:
    """Generate the launch description for the Franka robot controllers.

    Returns:
        LaunchDescription: The launch description containing the Franka controllers.
    """
    return LaunchDescription(
        [
            namespace_arg.declaration,
            enable_lock_unlock_arg.declaration,
            ip_address_arg.declaration,
            OpaqueFunction(function=launch_setup),
        ]
    )
