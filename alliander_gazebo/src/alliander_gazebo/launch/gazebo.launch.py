# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0


import xml.etree.ElementTree as ET
from typing import TypeVar

from alliander_gazebo.create_sdf import create_map_world
from alliander_gazebo.gazebo_ros_paths import GazeboRosPaths
from alliander_utilities.config_objects import Platform, PlatformList, SimulatorConfig
from alliander_utilities.launch_argument import LaunchArgument
from alliander_utilities.register import Register
from alliander_utilities.ros_utils import get_file_path
from launch import LaunchContext, LaunchDescription
from launch.actions import ExecuteProcess, OpaqueFunction
from launch_ros.actions import Node

config_arg = LaunchArgument("sim_config", "")
platform_list_arg = LaunchArgument("platform_list", "")


def get_sdf_file(world: str) -> str:
    """Define the sdf file used for the gazebo simulation.

    Args:
        world (str): The world argument.

    Returns:
        str: The path to the sdf file.

    Raises:
        ValueError: If the SDF file cannot be generated.

    """
    if world.startswith("map"):
        try:
            _, lon_str, lat_str = world.split("_")
        except ValueError as exc:
            raise ValueError(
                "Cannot generate world SDF. Use the format 'map_<lon>_<lat>' to create a map world."
            ) from exc
        try:
            lon = float(lon_str)
            lat = float(lat_str)
        except ValueError as exc:
            raise ValueError(
                "Cannot generate world SDF. Longitude and latitude must be valid float values."
            ) from exc
        create_map_world(lon, lat)
        return "/tmp/world.sdf"
    else:
        return get_file_path("alliander_gazebo", ["worlds"], world)


T = TypeVar("T", bound=Platform)


def get_bridge_topics(platforms: list[T]) -> list[str]:
    """Get the list of topics to bridge between ROS and Gazebo.

    Args:
        platforms (list[T]): The list of platforms in the simulation.

    Returns:
        list[str]: The list of topics to bridge.
    """
    bridge_topics = ["/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock"]
    for platform in platforms:
        if platform.platform_type == "Lidar":
            bridge_topics.append(
                f"/{platform.namespace}/scan/points@sensor_msgs/msg/PointCloud2@gz.msgs.PointCloudPacked"
            )
        if platform.platform_type == "Camera":
            bridge_topics.extend(
                [
                    f"/{platform.namespace}/color/camera_info@sensor_msgs/msg/CameraInfo@gz.msgs.CameraInfo",
                    f"/{platform.namespace}/color/image_raw@sensor_msgs/msg/Image@gz.msgs.Image",
                    f"/{platform.namespace}/depth/camera_info@sensor_msgs/msg/CameraInfo@gz.msgs.CameraInfo",
                    f"/{platform.namespace}/depth/image_rect_raw_float@sensor_msgs/msg/Image@gz.msgs.Image",
                ]
            )
        if platform.platform_type == "GPS":
            bridge_topics.append(
                f"/{platform.namespace}/gps/fix@sensor_msgs/msg/NavSatFix@gz.msgs.NavSat"
            )
    return bridge_topics


def launch_setup(context: LaunchContext) -> list:
    """The launch setup.

    Args:
        context (LaunchContext): The launch context.

    Returns:
        list: The actions to start.

    Raises:
        ValueError: If the SDF file does not contain a world attribute with a name.

    """
    config = SimulatorConfig.from_str(config_arg.string_value(context))
    platforms = PlatformList.from_str(platform_list_arg.string_value(context))

    sdf_file = get_sdf_file(config.world)
    sdf = ET.parse(sdf_file)
    world_attribute = sdf.getroot().find("world")
    if world_attribute is None:
        raise ValueError("sdf file should contain a world attribute with a name.")
    else:
        world_name = world_attribute.attrib.get("name")

    cmd = ["gz", "sim", sdf_file]
    if not config.load_ui:
        cmd.append("-s")
    gazebo = ExecuteProcess(
        cmd=cmd,
        shell=False,
        additional_env=GazeboRosPaths.get_env(),
    )

    bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=get_bridge_topics(platforms.platforms),
    )

    spawn_platforms = Node(
        package="alliander_gazebo",
        executable="spawn_platforms.py",
        parameters=[{"platform_config": platforms.to_str()}],
        output="screen",
    )

    unpause_sim = ExecuteProcess(
        cmd=[
            "gz",
            "service",
            "-s",
            f"/world/{world_name}/control",
            "--reqtype",
            "gz.msgs.WorldControl",
            "--reptype",
            "gz.msgs.Boolean",
            "--timeout",
            "3000",
            "--req",
            "pause: false",
        ],
        shell=False,
    )

    return [
        Register.on_start(gazebo, context),
        Register.on_log(
            bridge,
            "Creating GZ->ROS Bridge: [/clock (gz.msgs.Clock) -> /clock (rosgraph_msgs/msg/Clock)]",
            context,
        ),
        Register.on_log(spawn_platforms, "All platforms spawned!", context),
        Register.on_start(unpause_sim, context),
    ]


def generate_launch_description() -> LaunchDescription:
    """Generate the launch description for the Gazebo simulation with platforms.

    Returns:
        LaunchDescription: The launch description containing the actions to be executed.
    """
    return LaunchDescription(
        [
            config_arg.declaration,
            platform_list_arg.declaration,
            OpaqueFunction(function=launch_setup),
        ]
    )
