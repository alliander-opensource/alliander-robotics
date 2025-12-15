# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

import os

from launch import LaunchContext, LaunchDescription
from launch.actions import OpaqueFunction
from launch_ros.actions import ComposableNodeContainer, Node
from launch_ros.descriptions import ComposableNode
from rcdt_utilities.launch_argument import LaunchArgument
from rcdt_utilities.launch_utils import SKIP
from rcdt_utilities.register import Register, RegisteredLaunchDescription
from rcdt_utilities.ros_utils import get_file_path

use_sim_arg = LaunchArgument("simulation", True, [True, False])
namespace_arg = LaunchArgument("namespace", "zed")


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
    namespace = "zed"

    # use_sim = use_sim_arg.bool_value(context)
    # namespace = namespace_arg.string_value(context)

    description = RegisteredLaunchDescription(
        get_file_path("rcdt_zed", ["launch"], "description.launch.py")
    )

    map_link = create_map_link("zed", (0, 0, 0), (0, 0, 0))

    convert_32FC1_to_16UC1_node = Node(  # noqa: N806
        package="rcdt_utilities",
        executable="convert_32FC1_to_16UC1",
        namespace=namespace,
    )

    # ZED Node parameters
    common_cfg = get_file_path("rcdt_description", ["config"], "common_stereo.yaml")
    camera_cfg = get_file_path("zed_wrapper", ["config"], "zed2i.yaml")
    ffmpeg_cfg = get_file_path("zed_wrapper", ["config"], "ffmpeg.yaml")

    node_parameters = [
        common_cfg,
        camera_cfg,
        ffmpeg_cfg,
        {
            # Required identification
            "general.camera_name": f"{namespace}/{namespace}",
            "general.camera_model": "zed2i",
            "general.camera_id": -1,
            "pos_tracking.enable_tracking": False,
            "depth.depth_stabilization": 0,
            "pos_tracking.publish_tf": False,
            "pos_tracking.publish_map_tf": False,
        },
    ]

    # Zed Composable Node
    zed_node = ComposableNode(
        package="zed_components",
        plugin="stereolabs::ZedCamera",
        name=namespace,
        parameters=node_parameters,
        remappings=[
            (f"/{namespace}/left/camera_info", f"/{namespace}/color/camera_info"),
            (
                f"/{namespace}/left/image_rect_color",
                f"/{namespace}/color/image_raw",
            ),
            (
                f"/{namespace}/depth/depth_registered",
                f"/{namespace}/depth/image_rect_raw",
            ),
        ],
        extra_arguments=[{"use_intra_process_comms": True}],
    )

    # Zed Composable Node Container
    zed_container = ComposableNodeContainer(
        name="zed_container",
        namespace=namespace,
        package="rclcpp_components",
        executable="component_container_mt",
        composable_node_descriptions=[zed_node],
        output="screen",
    )

    return [
        Register.group(description, context),
        Register.on_start(map_link, context),
        Register.on_start(convert_32FC1_to_16UC1_node, context) if use_sim else SKIP,
        Register.on_start(zed_container, context) if not use_sim else SKIP,
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
