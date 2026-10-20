# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0


import xml.etree.ElementTree as ET

from alliander_gazebo.bridge_config import BridgeConfig
from alliander_gazebo.create_sdf import create_map_world
from alliander_gazebo.gazebo_ros_paths import GazeboRosPaths
from alliander_utilities.config_objects import GPS, PlatformList, SimulatorConfig
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

    cmd: list[str] = ["gz", "sim", sdf_file]
    if not config.load_ui:
        cmd.append("-s")
    gazebo = ExecuteProcess(
        cmd=cmd,
        shell=False,
        additional_env=GazeboRosPaths.get_env(),  # ty: ignore
    )

    bridge_config = BridgeConfig("/tmp/gz_bridge_config.yaml")
    bridge_config.create_bridge_config(platforms.platforms)
    bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        parameters=[{"config_file": bridge_config.config_file}],
    )

    bridge_image = Node(
        package="ros_gz_image",
        executable="image_bridge",
        arguments=bridge_config.image_topics,
        remappings=bridge_config.image_remaps,
    )

    spawn_platforms = Node(
        package="alliander_gazebo",
        executable="spawn_platforms.py",
        parameters=[{"platform_config": platforms.to_str()}],
        output="screen",
    )

    # Republish GPS fixes with covariance (Gazebo plugin doesn't provide any) to make navsat_transform work properly in simulation
    gps_platforms = [c for c in platforms.platforms if c.__class__ == GPS]
    navsat_covariance_nodes = []
    for gps in gps_platforms:
        namespace_gps = gps.namespace
        navsat_covariance_nodes.append(
            Node(
                package="alliander_gazebo",
                executable="navsat_covariance_node",
                namespace=namespace_gps,
                remappings=[
                    ("gps/fix_in", f"/{namespace_gps}/gps/fix_raw"),
                    ("gps/fix_out", f"/{namespace_gps}/gps/fix"),
                ],
            )
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
        Register.on_start(bridge_image, context),
        Register.on_log(spawn_platforms, "All platforms spawned!", context),
        *[Register.on_start(node, context) for node in navsat_covariance_nodes],
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
