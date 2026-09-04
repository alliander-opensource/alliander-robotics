# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0


from alliander_utilities.launch_argument import LaunchArgument
from alliander_utilities.register import Register
from launch import LaunchContext, LaunchDescription
from launch.actions import OpaqueFunction
from launch_ros.actions import ComposableNodeContainer, Node
from launch_ros.descriptions import ComposableNode

platform_arg = LaunchArgument("platform_config", "")


def launch_setup(context: LaunchContext) -> list:  # noqa: PLR0912, PLR0915
    """The launch setup.

    Args:
        context (LaunchContext): The launch context.

    Returns:
        list: The actions to start.
    """
    apriltag_node = ComposableNode(
        package="isaac_ros_apriltag",
        plugin="nvidia::isaac_ros::apriltag::AprilTagNode",
        name="apriltag",
        remappings=[
            ("/image", "/zed/color/image_raw"),
            ("/camera_info", "/zed/color/camera_info"),
        ],
    )

    apriltag_container = ComposableNodeContainer(
        package="rclcpp_components",
        name="apriltag_container",
        namespace="",
        executable="component_container_mt",
        composable_node_descriptions=[
            apriltag_node,
        ],
        output="screen",
    )

    apriltag_manager = Node(
        package="alliander_isaac",
        executable="apriltag_manager",
    )

    return [
        Register.on_start(apriltag_container, context),
        Register.on_start(apriltag_manager, context),
    ]


def generate_launch_description() -> LaunchDescription:
    """Generate the launch description for the navigation stack.

    Returns:
        LaunchDescription: The launch description containing the actions to be executed.
    """
    return LaunchDescription(
        [
            platform_arg.declaration,
            OpaqueFunction(function=launch_setup),
        ]
    )
