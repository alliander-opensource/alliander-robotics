# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

from launch import LaunchContext, LaunchDescription
from launch.actions import OpaqueFunction
from rcdt_utilities.config_objects import Arm
from rcdt_utilities.launch_argument import LaunchArgument
from rcdt_utilities.launch_utils import SKIP, state_publisher_node, static_tf_node
from rcdt_utilities.register import Register, RegisteredLaunchDescription
from rcdt_utilities.ros_utils import get_file_path

platform_arg = LaunchArgument("platform_config", "")


def launch_setup(context: LaunchContext) -> list:
    """The launch setup.

    Args:
        context (LaunchContext): The launch context.

    Returns:
        list: The actions to start.
    """
    arm_config = Arm.from_str(platform_arg.string_value(context))

    state_publisher = state_publisher_node(
        namespace=arm_config.namespace,
        platform="franka",
        xacro="franka.urdf.xacro",
        xacro_arguments={
            "simulation": str(arm_config.simulation),
            "ip_address": arm_config.ip_address,
            "namespace": arm_config.namespace,
            "parent": "" if arm_config.parent.link else "world",
            "connected_to": "" if arm_config.parent.link else "world",
            "childs": str(
                [
                    [child.connects_to, child.namespace, child.link]
                    for child in arm_config.childs
                ]
            ),
        },
    )

    parent = arm_config.parent
    static_tf = static_tf_node(
        parent_frame=f"{parent.namespace}/{parent.link}" if parent.link else "map",
        child_frame=f"{arm_config.namespace}/{parent.connects_to}",
        position=arm_config.position,
        orientation=arm_config.orientation,
    )

    hardware = RegisteredLaunchDescription(
        get_file_path("rcdt_franka", ["launch"], "hardware.launch.py"),
        launch_arguments={"platform_config": arm_config.to_str()},
    )

    controllers = RegisteredLaunchDescription(
        get_file_path("rcdt_franka", ["launch"], "controllers.launch.py"),
        launch_arguments={"platform_config": arm_config.to_str()},
    )

    gripper = RegisteredLaunchDescription(
        get_file_path("rcdt_franka", ["launch"], "gripper_services.launch.py"),
        launch_arguments={"namespace": arm_config.namespace},
    )

    return [
        Register.on_start(state_publisher, context),
        Register.on_start(static_tf, context),
        Register.group(hardware, context) if not arm_config.simulation else SKIP,
        Register.group(controllers, context),
        Register.group(gripper, context),
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
