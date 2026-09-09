# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0


from alliander_utilities.config_objects import Apriltag, Camera, PlatformList
from alliander_utilities.launch_argument import LaunchArgument
from alliander_utilities.register import Register
from launch import LaunchContext, LaunchDescription
from launch.actions import OpaqueFunction
from launch_ros.actions import ComposableNodeContainer, Node
from launch_ros.descriptions import ComposableNode
from termcolor import colored

platform_list_arg = LaunchArgument("platform_list", "")


def launch_setup(context: LaunchContext) -> list:  # noqa: PLR0912, PLR0915
    """The launch setup.

    Args:
        context (LaunchContext): The launch context.

    Returns:
        list: The actions to start.
    """
    platform_list = PlatformList.from_str(platform_list_arg.string_value(context))

    cameras = [
        platform for platform in platform_list.platforms if isinstance(platform, Camera)
    ]
    if len(cameras) == 0:
        print(colored("No cameras defined. Apriltag detection will not work.", "red"))
        return []
    elif len(cameras) > 1:
        print(colored("Multiple cameras defined. Using the first one.", "yellow"))
    image_topic = f"/{cameras[0].namespace}/color/image_raw"
    camera_info_topic = f"/{cameras[0].namespace}/color/camera_info"

    apriltag_node = ComposableNode(
        package="isaac_ros_apriltag",
        plugin="nvidia::isaac_ros::apriltag::AprilTagNode",
        name="apriltag",
        remappings=[
            ("/image", image_topic),
            ("/camera_info", camera_info_topic),
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

    apriltags = [
        platform
        for platform in platform_list.platforms
        if isinstance(platform, Apriltag)
    ]

    apriltag_manager = Node(
        package="alliander_apriltag",
        executable="apriltag_manager",
        parameters=[
            {
                "tag_ids": [apriltag.id for apriltag in apriltags],
                "publish_topics": [apriltag.publish_topic for apriltag in apriltags],
            }
        ],
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
            platform_list_arg.declaration,
            OpaqueFunction(function=launch_setup),
        ]
    )
