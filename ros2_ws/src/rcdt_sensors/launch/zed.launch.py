# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

from launch import LaunchContext, LaunchDescription
from launch.actions import OpaqueFunction
from launch_ros.actions import ComposableNodeContainer, Node
from launch_ros.descriptions import ComposableNode
from rcdt_utilities.launch_argument import LaunchArgument
from rcdt_utilities.register import Register
from rcdt_utilities.ros_utils import get_file_path

namespace_arg = LaunchArgument("namespace", "zed")
use_sim_arg = LaunchArgument("simulation", True, [True, False])


def launch_setup(context: LaunchContext) -> list:
    """Setup the launch description for the ZED camera.

    Args:
        context (LaunchContext): The launch context.

    Returns:
        list: A list of actions to be executed.
    """
    namespace = namespace_arg.string_value(context)
    use_sim = use_sim_arg.bool_value(context)

    # ZED Node parameters
    common_cfg = get_file_path("rcdt_sensors", ["config"], "common_stereo.yaml")
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

    if use_sim:
        convert_32FC1_to_16UC1_node = Node(  # noqa: N806
            package="rcdt_sensors",
            executable="convert_32FC1_to_16UC1",
            namespace=namespace,
        )
        zed = LaunchDescription(
            [
                Register.on_start(convert_32FC1_to_16UC1_node, context),
            ]
        )
    else:
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
        # Define the container
        zed_container = ComposableNodeContainer(
            name="zed_container",
            namespace=namespace,
            package="rclcpp_components",
            executable="component_container_mt",
            composable_node_descriptions=[zed_node],
            output="screen",
        )
        zed = LaunchDescription([Register.on_start(zed_container, context)])

    return [zed]


def generate_launch_description() -> LaunchDescription:
    """Generate the launch description for the ZED camera.

    Returns:
        LaunchDescription: The launch description for the ZED camera.
    """
    return LaunchDescription(
        [
            namespace_arg.declaration,
            use_sim_arg.declaration,
            OpaqueFunction(function=launch_setup),
        ]
    )
