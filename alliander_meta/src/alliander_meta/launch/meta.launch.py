# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0
import warnings

from alliander_utilities.config_objects import PlatformList
from alliander_utilities.launch_argument import LaunchArgument
from alliander_utilities.register import Register
from launch import LaunchContext, LaunchDescription
from launch.actions import OpaqueFunction
from launch_ros.actions import Node, SetParameter

platform_list_arg = LaunchArgument("platform_list", "")


def launch_setup(context: LaunchContext) -> list:
    """The launch setup.

    Args:
        context (LaunchContext): The launch context.

    Returns:
        list: The actions to start.
    """
    platforms = PlatformList.from_str(platform_list_arg.string_value(context)).platforms

    namespace = "quest"
    namespace_arm = ""

    for platform in platforms:
        match platform.platform_type:
            case "Arm":
                if not namespace_arm:
                    namespace_arm = platform.namespace
                else:
                    warnings.warn(
                        "No support for multiple arms yet, only accepting the first arm.",
                        RuntimeWarning,
                        stacklevel=1,
                    )
            case _:
                pass

    ros_tcp_endpoint = Node(
        package="ros_tcp_endpoint",
        executable="default_server_endpoint",
        emulate_tty=True,
        parameters=[{"ROS_IP": "10.223.237.24"}, {"ROS_TCP_PORT": 10000}],
        namespace=namespace,
        remappings=[
            ("/tf", f"/{namespace}/tf"),
            ("/tf_static", f"/{namespace}/tf_static"),
        ],
    )

    meta_manager = Node(
        package="alliander_meta",
        executable="meta_manager",
        namespace=namespace,
        parameters=[{"namespace_arm": namespace_arm}],
    )

    return [
        SetParameter(name="use_sim_time", value=platforms[0].simulation),
        Register.on_start(ros_tcp_endpoint, context),
        Register.on_start(meta_manager, context),
    ]


def generate_launch_description() -> LaunchDescription:
    """Generate the launch description.

    Returns:
        LaunchDescription: The launch description.
    """
    return LaunchDescription(
        [
            platform_list_arg.declaration,
            OpaqueFunction(function=launch_setup),
        ]
    )
