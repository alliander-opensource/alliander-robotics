# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0
from alliander_utilities.launch_argument import LaunchArgument
from alliander_utilities.register import Register
from launch import LaunchContext, LaunchDescription
from launch.actions import OpaqueFunction
from launch_ros.actions import Node, SetParameter

platform_arg = LaunchArgument("platform_config", "")


def launch_setup(context: LaunchContext) -> list:
    """The launch setup.

    Args:
        context (LaunchContext): The launch context.

    Returns:
        list: The actions to start.
    """
    namespace = "quest"
    namespace_arm = "franka"
    use_sim_time = True

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
        SetParameter(name="use_sim_time", value=use_sim_time),
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
            platform_arg.declaration,
            OpaqueFunction(function=launch_setup),
        ]
    )
