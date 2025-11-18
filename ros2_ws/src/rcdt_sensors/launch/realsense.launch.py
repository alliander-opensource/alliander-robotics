# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

from launch import LaunchContext, LaunchDescription
from launch.actions import OpaqueFunction
from launch_ros.actions import Node
from rcdt_utilities.launch_argument import LaunchArgument
from rcdt_utilities.register import Register

use_sim_arg = LaunchArgument("simulation", True, [True, False])
namespace_arg = LaunchArgument("namespace", "realsense")


def launch_setup(context: LaunchContext) -> list:
    """Setup the launch description for the realsense camera.

    Args:
        context (LaunchContext): The launch context.

    Returns:
        list: A list of actions to be executed.
    """
    use_sim = use_sim_arg.bool_value(context)
    namespace = namespace_arg.string_value(context)

    if use_sim:
        convert_32FC1_to_16UC1_node = Node(  # noqa: N806
            package="rcdt_sensors",
            executable="convert_32FC1_to_16UC1",
            namespace=namespace,
        )
        return [
            Register.on_start(convert_32FC1_to_16UC1_node, context),
        ]
    else:
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
        realsense = LaunchDescription(
            [Register.on_start(realsense2_camera_node, context)]
        )

        return [realsense]


def generate_launch_description() -> LaunchDescription:
    """Generate the launch description for the realsense camera.

    Returns:
        LaunchDescription: The launch description for the realsense camera.
    """
    return LaunchDescription(
        [
            use_sim_arg.declaration,
            namespace_arg.declaration,
            OpaqueFunction(function=launch_setup),
        ]
    )
