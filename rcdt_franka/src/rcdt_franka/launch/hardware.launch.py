# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

from launch import LaunchContext, LaunchDescription
from launch.actions import OpaqueFunction, Shutdown
from launch_ros.actions import Node
from rcdt_utilities.config_objects import Arm
from rcdt_utilities.launch_argument import LaunchArgument
from rcdt_utilities.register import Register
from rcdt_utilities.ros_utils import get_file_path

platform_arg = LaunchArgument("platform_config", "")
enable_lock_unlock = False


def launch_setup(context: LaunchContext) -> list:
    """Setup the launch description for the Franka robot controllers.

    Args:
        context (LaunchContext): The launch context.

    Returns:
        list: A list of actions to be executed in the launch description.
    """
    arm_config = Arm.from_str(platform_arg.string_value(context))

    ns: str = f"/{arm_config.namespace}" if arm_config.namespace else ""

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
        namespace=arm_config.namespace,
        on_exit=Shutdown(),
    )

    settings_setter = Node(
        package="rcdt_franka",
        executable="settings_setter.py",
        namespace=arm_config.namespace,
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
        namespace=arm_config.namespace,
    )

    return [
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
            platform_arg.declaration,
            OpaqueFunction(function=launch_setup),
        ]
    )
