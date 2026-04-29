# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0
from alliander_utilities.config_objects import Lift
from alliander_utilities.launch_argument import LaunchArgument
from alliander_utilities.launch_utils import SKIP, state_publisher_node, static_tf_node
from alliander_utilities.register import Register, RegisteredLaunchDescription
from alliander_utilities.ros_utils import get_file_path
from launch import LaunchContext, LaunchDescription
from launch.actions import OpaqueFunction
from launch_ros.actions import SetParameter

platform_arg = LaunchArgument("platform_config", "")


def launch_setup(context: LaunchContext) -> list:
    """The launch setup.

    Args:
        context (LaunchContext): The launch context.

    Returns:
        list: The actions to start.
    """
    lift_config = Lift.from_str(platform_arg.string_value(context))

    state_publisher = state_publisher_node(
        namespace=lift_config.namespace,
        platform="ewellix",
        xacro="ewellix.urdf.xacro",
        xacro_arguments={
            "namespace": lift_config.namespace,
            "sim_gazebo": str(lift_config.simulation),
            "parent": "" if lift_config.parent.link else "world",
            "childs": str(
                [
                    [child.connects_to, child.namespace, child.link]
                    for child in lift_config.childs
                ]
            ),
        },
    )

    parent = lift_config.parent
    static_tf = static_tf_node(
        parent_frame=f"{parent.namespace}/{parent.link}" if parent.link else "map",
        child_frame=f"{lift_config.namespace}/{lift_config.default_link_to_parent()}",
        position=lift_config.position,
        orientation=lift_config.orientation,
    )

    hardware = RegisteredLaunchDescription(
        get_file_path("alliander_ewellix", ["launch"], "hardware.launch.py"),
        launch_arguments={"platform_config": lift_config.to_str()},
    )

    controllers = RegisteredLaunchDescription(
        get_file_path("alliander_ewellix", ["launch"], "controllers.launch.py"),
        launch_arguments={"platform_config": lift_config.to_str()},
    )

    return [
        SetParameter(name="use_sim_time", value=lift_config.simulation),
        Register.on_start(state_publisher, context),
        Register.on_start(static_tf, context),
        Register.group(hardware, context) if not lift_config.simulation else SKIP,
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
