# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

from launch import LaunchContext, LaunchDescription
from launch.actions import OpaqueFunction
from launch_ros.actions import Node
from rcdt_utilities.launch_argument import LaunchArgument

namespace_arm_arg = LaunchArgument("namespace_arm", "")
namespace_camera_arg = LaunchArgument("namespace_camera", "")


def launch_setup(context: LaunchContext) -> list:
    """This launch file starts two topic_tools relay nodes to pass depth images and camera info from a camera to an arm.

    A move_group of the arm can use these topics to build an octomap.
    This launch file is launched as a separate process from the MoveitManager class.

    Args:
        context (LaunchContext): The launch context.

    Returns:
        list: A list of actions to be executed in the launch description.
    """
    namespace_arm = namespace_arm_arg.string_value(context)
    namespace_camera = namespace_camera_arg.string_value(context)

    relay_depth_image = Node(
        package="topic_tools",
        executable="relay",
        name="relay_depth_image",
        namespace=namespace_arm,
        arguments=[
            f"/{namespace_camera}/depth/image_rect_raw",
            f"/{namespace_arm}/octomap/depth_image",
        ],
    )

    relay_camera_info = Node(
        package="topic_tools",
        executable="relay",
        name="relay_camera_info",
        namespace=namespace_arm,
        arguments=[
            f"/{namespace_camera}/depth/camera_info",
            f"/{namespace_arm}/octomap/camera_info",
        ],
    )

    return [relay_depth_image, relay_camera_info]


def generate_launch_description() -> LaunchDescription:
    """Generate the launch description.

    Returns:
        LaunchDescription: The launch description.
    """
    return LaunchDescription(
        [
            namespace_arm_arg.declaration,
            namespace_camera_arg.declaration,
            OpaqueFunction(function=launch_setup),
        ]
    )
