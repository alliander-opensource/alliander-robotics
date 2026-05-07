# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

from alliander_utilities.launch_argument import LaunchArgument
from alliander_utilities.register import Register
from alliander_utilities.ros_utils import get_file_path
from launch import LaunchContext, LaunchDescription
from launch.actions import OpaqueFunction
from launch_ros.actions import ComposableNodeContainer
from launch_ros.descriptions import ComposableNode

namespace_arg = LaunchArgument("namespace", "")


def launch_setup(context: LaunchContext) -> list:
    """The launch setup.

    Args:
        context (LaunchContext): The launch context.

    Returns:
        list: The actions to start.
    """
    namespace = namespace_arg.string_value(context)

    # ZED Node parameters
    common_cfg = get_file_path(
        "alliander_description", ["zed", "config"], "common_stereo.yaml"
    )
    camera_cfg = get_file_path("zed_wrapper", ["config"], "zed2i.yaml")

    node_parameters = [
        common_cfg,
        camera_cfg,
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
        Register.on_start(zed_container, context),
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
