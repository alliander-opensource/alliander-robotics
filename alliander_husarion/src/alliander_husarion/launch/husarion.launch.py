# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

from alliander_utilities.config_objects import Vehicle
from alliander_utilities.launch_argument import LaunchArgument
from alliander_utilities.launch_utils import SKIP, state_publisher_node, static_tf_node
from alliander_utilities.register import Register, RegisteredLaunchDescription
from alliander_utilities.ros_utils import get_file_path
from launch import LaunchContext, LaunchDescription
from launch.actions import ExecuteProcess, OpaqueFunction
from launch_ros.actions import Node, SetParameter

platform_arg = LaunchArgument("platform_config", "")


def launch_setup(context: LaunchContext) -> list:
    """The launch setup.

    Args:
        context (LaunchContext): The launch context.

    Returns:
        list: The actions to start.
    """
    vehicle_config = Vehicle.from_str(platform_arg.string_value(context))
    parent = vehicle_config.parent

    state_publisher = state_publisher_node(
        namespace=vehicle_config.namespace,
        platform="husarion",
        xacro=f"{vehicle_config.name}.urdf.xacro",
        xacro_arguments={
            "childs": str(
                [
                    [child.connects_to, child.namespace, child.link]
                    for child in vehicle_config.childs
                ]
            ),
        },
    )

    parent = vehicle_config.parent
    static_tf = static_tf_node(
        parent_frame=f"{parent.namespace}/{parent.link}" if parent.link else "map",
        child_frame=f"{vehicle_config.namespace}/{parent.connects_to}",
        position=vehicle_config.position,
        orientation=vehicle_config.orientation,
    )

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
        remappings=[("cmd_vel_out", "cmd_vel")],
    )

    controllers = RegisteredLaunchDescription(
        get_file_path("alliander_husarion", ["launch"], "controllers.launch.py")
    )

    # In some configurations, no nodes will be started.
    # Since other containers depend on a healthy Husarion container,
    # we can sleep infinity to keep the container active in healthy state:
    sleep_infinity = ExecuteProcess(cmd=["sleep", "infinity"])

    return [
        SetParameter(name="use_sim_time", value=vehicle_config.simulation),
        Register.on_start(state_publisher, context)
        if vehicle_config.simulation
        else SKIP,
        Register.on_start(static_tf, context) if not vehicle_config.nav2 else SKIP,
        Register.on_start(twist_mux, context),
        Register.group(controllers, context) if vehicle_config.simulation else SKIP,
        Register.on_start(sleep_infinity, context),
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
