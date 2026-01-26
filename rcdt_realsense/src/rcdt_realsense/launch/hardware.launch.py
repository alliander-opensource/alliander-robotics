# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

from launch import LaunchContext, LaunchDescription
from launch.actions import OpaqueFunction
from launch_ros.actions import Node
from rcdt_utilities.launch_argument import LaunchArgument
from rcdt_utilities.register import Register

namespace_arg = LaunchArgument("namespace", "")


def launch_setup(context: LaunchContext) -> list:
    """The launch setup.

    Args:
        context (LaunchContext): The launch context.

    Returns:
        list: The actions to start.
    """
    namespace = namespace_arg.string_value(context)

    realsense2_camera_node = Node(
        package="realsense2_camera",
        executable="realsense2_camera_node",
        namespace=namespace,
        parameters=[
            {
                "enable_infra": False,
                "enable_infra1": False,
                "enable_infra2": False,
                "enable_accel": False,
                "enable_gyro": False,
                "enable_rgbd": True,
                "enable_sync": True,
                "align_depth.enable": True,
                "tf_prefix": namespace + "/",
                "rgb_camera.color_profile": "640,480,60",
                "depth_module.depth_profile": "640,480,60",
            }
        ],
        remappings=[
            (
                f"/{namespace}/camera/color/image_raw",
                f"/{namespace}/color/image_raw",
            ),
            (
                f"/{namespace}/camera/color/camera_info",
                f"/{namespace}/color/camera_info",
            ),
            (
                f"/{namespace}/camera/depth/camera_info",
                f"/{namespace}/depth/camera_info",
            ),
            (
                f"/{namespace}/camera/aligned_depth_to_color/image_raw",
                f"/{namespace}/depth/image_rect_raw",
            ),
            (f"/{namespace}/camera/rgbd", f"/{namespace}/rgbd"),
        ],
    )

    return [
        Register.on_start(realsense2_camera_node, context),
    ]


def generate_launch_description() -> LaunchDescription:
    """Generate the launch description.

    Returns:
        LaunchDescription: The launch description.
    """
    return LaunchDescription(
        [
            namespace_arg.declaration,
            OpaqueFunction(function=launch_setup),
        ]
    )
