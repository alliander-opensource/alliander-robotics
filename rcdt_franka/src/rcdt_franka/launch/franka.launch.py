# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

from launch import LaunchContext, LaunchDescription
from launch.actions import OpaqueFunction
from rcdt_utilities.config_objects import Arm
from rcdt_utilities.launch_argument import LaunchArgument
from rcdt_utilities.launch_utils import state_publisher_node, static_tf_node
from rcdt_utilities.register import Register, RegisteredLaunchDescription
from rcdt_utilities.ros_utils import get_file_path

config_arg = LaunchArgument("config", "")


def launch_setup(context: LaunchContext) -> list:
    """The launch setup.

    Args:
        context (LaunchContext): The launch context.

    Returns:
        list: The actions to start.
    """
    configuration = Arm.from_str(config_arg.string_value(context))

    state_publisher = state_publisher_node(
        namespace=configuration.namespace,
        platform="franka",
        xacro="franka.urdf.xacro",
        xacro_arguments={
            "simulation": str(configuration.simulation),
            "namespace": configuration.namespace,
            "parent": "" if configuration.parent.link else "world",
            "childs": str(
                [
                    [child.connects_to, child.namespace, child.link]
                    for child in configuration.childs
                ]
            ),
        },
    )

    parent = configuration.parent
    static_tf = static_tf_node(
        parent_frame=f"{parent.namespace}/{parent.link}" if parent.link else "map",
        child_frame=f"{configuration.namespace}/{parent.connects_to}",
        position=configuration.position,
        orientation=configuration.orientation,
    )

    controllers = RegisteredLaunchDescription(
        get_file_path("rcdt_franka", ["launch"], "controllers.launch.py")
    )

    gripper = RegisteredLaunchDescription(
        get_file_path("rcdt_franka", ["launch"], "gripper_services.launch.py"),
        launch_arguments={"namespace": configuration.namespace},
    )

    return [
        Register.on_start(state_publisher, context),
        Register.on_start(static_tf, context),
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
            config_arg.declaration,
            OpaqueFunction(function=launch_setup),
        ]
    )
