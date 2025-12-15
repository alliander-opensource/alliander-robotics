# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

import os

from launch import LaunchContext, LaunchDescription
from launch.actions import OpaqueFunction
from launch_ros.actions import Node
from rcdt_utilities.launch_argument import LaunchArgument
from rcdt_utilities.launch_utils import SKIP
from rcdt_utilities.register import Register, RegisteredLaunchDescription
from rcdt_utilities.ros_utils import get_file_path

use_sim_arg = LaunchArgument("simulation", True, [True, False])
namespace_arg = LaunchArgument("namespace", "realsense")


def create_map_link(namespace: str, position: tuple, orientation: tuple) -> Node:
    """Create a static_transform_publisher node that links the platform to the map.

    Returns:
        Node: A static_transform_publisher node that links the platform with the world or None if not applicable.
    """
    return Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        name="static_tf_world",
        arguments=[
            "--frame-id",
            "map",
            "--child-frame-id",
            f"{namespace}/base_link",
            "--x",
            f"{position[0]}",
            "--y",
            f"{position[1]}",
            "--z",
            f"{position[2]}",
            "--roll",
            f"{orientation[0]}",
            "--pitch",
            f"{orientation[1]}",
            "--yaw",
            f"{orientation[2]}",
        ],
    )


def launch_setup(context: LaunchContext) -> list:
    simulation = os.environ.get("SIMULATION", default="False").lower() == "true"

    use_sim = simulation
    namespace = "realsense"

    # use_sim = use_sim_arg.bool_value(context)
    # namespace = namespace_arg.string_value(context)

    description = RegisteredLaunchDescription(
        get_file_path("rcdt_realsense", ["launch"], "description.launch.py")
    )

    map_link = create_map_link("realsense", (0, 0, 0), (0, 0, 0))

    convert_32FC1_to_16UC1_node = Node(  # noqa: N806
        package="rcdt_utilities",
        executable="convert_32FC1_to_16UC1",
        namespace=namespace,
    )

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
        Register.group(description, context),
        Register.on_start(map_link, context),
        Register.on_start(convert_32FC1_to_16UC1_node, context) if use_sim else SKIP,
        Register.on_start(realsense2_camera_node, context) if not use_sim else SKIP,
    ]


def generate_launch_description() -> LaunchDescription:
    """Generate the launch description for the Panther robot.

    Returns:
        LaunchDescription: The launch description for the Panther robot.
    """
    return LaunchDescription(
        [
            use_sim_arg.declaration,
            namespace_arg.declaration,
            OpaqueFunction(function=launch_setup),
        ]
    )
