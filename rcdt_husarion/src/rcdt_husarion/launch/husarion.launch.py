# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

from launch import LaunchContext, LaunchDescription
from launch.actions import ExecuteProcess, OpaqueFunction
from rcdt_utilities.config_objects import Vehicle
from rcdt_utilities.launch_argument import LaunchArgument
from rcdt_utilities.launch_utils import SKIP, state_publisher_node, static_tf_node
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
    config = Vehicle.from_str(config_arg.string_value(context))
    parent = config.parent

    state_publisher = state_publisher_node(
        namespace=config.namespace,
        platform="husarion",
        xacro=f"{config.name}.urdf.xacro",
        xacro_arguments={
            "childs": str(
                [
                    [child.connects_to, child.namespace, child.link]
                    for child in config.childs
                ]
            ),
        },
    )

    parent = config.parent
    static_tf = static_tf_node(
        parent_frame=f"{parent.namespace}/{parent.link}" if parent.link else "map",
        child_frame=f"{config.namespace}/{parent.connects_to}",
        position=config.position,
        orientation=config.orientation,
    )

    controllers = RegisteredLaunchDescription(
        get_file_path("rcdt_husarion", ["launch"], "controllers.launch.py")
    )

    # In some configurations, no nodes will be started.
    # Since other containers depend on a healthy Husarion container,
    # we can sleep infinity to keep the container active in healthy state:
    sleep_infinity = ExecuteProcess(cmd=["sleep", "infinity"])

    return [
        Register.on_start(state_publisher, context) if config.simulation else SKIP,
        Register.on_start(static_tf, context) if not config.nav2 else SKIP,
        Register.group(controllers, context) if config.simulation else SKIP,
        Register.on_start(sleep_infinity, context),
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
