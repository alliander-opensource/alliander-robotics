# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

from alliander_utilities.config_objects import Arm
from alliander_utilities.launch_argument import LaunchArgument
from alliander_utilities.launch_utils import state_publisher_node, static_tf_node
from alliander_utilities.register import Register, RegisteredLaunchDescription
from alliander_utilities.ros_utils import get_file_path
from launch import LaunchContext, LaunchDescription
from launch.actions import OpaqueFunction

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
        platform="ur",
        xacro="ur.urdf.xacro",
        xacro_arguments={
            "simulation": str(arm_config.simulation),
            "simulation_controllers": get_file_path(
                "alliander_description", ["ur", "config"], "controllers.yaml"
            ),
            "ros_namespace": arm_config.namespace,
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

    controllers = RegisteredLaunchDescription(
        get_file_path("alliander_ur", ["launch"], "controllers.launch.py"),
        launch_arguments={"platform_config": arm_config.to_str()},
    )

    return [
        Register.on_start(state_publisher, context),
        Register.on_start(static_tf, context),
        Register.group(controllers, context),
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
