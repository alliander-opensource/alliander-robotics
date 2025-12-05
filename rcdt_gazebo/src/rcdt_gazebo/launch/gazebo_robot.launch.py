# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0


import xml.etree.ElementTree as ET

from launch import LaunchContext, LaunchDescription
from launch.actions import ExecuteProcess, OpaqueFunction
from launch_ros.actions import Node
from rcdt_gazebo.create_sdf import create_map_world
from rcdt_gazebo.gazebo_ros_paths import GazeboRosPaths
from rcdt_utilities.launch_argument import LaunchArgument
from rcdt_utilities.register import Register
from rcdt_utilities.ros_utils import get_file_path
import xacro

load_gazebo_ui_arg = LaunchArgument("load_gazebo_ui", False, [True, False])
world_arg = LaunchArgument("world", "empty.sdf")
platforms_arg = LaunchArgument("platforms", "")
positions_arg = LaunchArgument("positions", "")
orientations_arg = LaunchArgument("orientations", "")
parents_arg = LaunchArgument("parents", "")
parent_links_arg = LaunchArgument("parent_links", "")
bridge_topics_arg = LaunchArgument("bridge_topics", "")


def get_robot_description(
    xacro_path: str, xacro_arguments: dict | None = None, semantic: bool = False
) -> dict:
    """Process a Xacro file to generate the robot description.

    Args:
        xacro_path (str): The path to the Xacro file.
        xacro_arguments (dict | None): A dictionary of arguments to pass to the Xacro processor.
        semantic (bool): Whether to return the semantic robot description.

    Returns:
        dict: A dictionary containing the robot description in XML format.
    """
    if xacro_arguments is None:
        xacro_arguments = {}
    robot_description_config = xacro.process_file(xacro_path, mappings=xacro_arguments)
    name = "robot_description_semantic" if semantic else "robot_description"
    return {name: robot_description_config.toxml()}


def launch_setup(context: LaunchContext) -> list:
    """Setup the launch description for the Gazebo simulation with platforms.

    Args:
        context (LaunchContext): The launch context.

    Raises:
        ValueError: If the SDF file does not contain a world attribute with a name.

    Returns:
        list: A list of actions to be executed in the launch description.
    """
    load_gazebo_ui = load_gazebo_ui_arg.bool_value(context)
    world = world_arg.string_value(context)
    platforms = platforms_arg.string_value(context)
    positions = positions_arg.string_value(context)
    orientations = orientations_arg.string_value(context)
    parents = parents_arg.string_value(context)
    parent_links = parent_links_arg.string_value(context)
    bridge_topics = bridge_topics_arg.string_value(context).split()

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
        sdf_file = "/tmp/world.sdf"
    else:
        sdf_file = get_file_path("rcdt_gazebo", ["worlds"], world)
    sdf = ET.parse(sdf_file)
    world_attribute = sdf.getroot().find("world")
    if world_attribute is None:
        raise ValueError("sdf file should contain a world attribute with a name.")
    else:
        world_name = world_attribute.attrib.get("name")
    cmd = ["gz", "sim", sdf_file]
    if not load_gazebo_ui:
        cmd.append("-s")
    gazebo = ExecuteProcess(
        cmd=cmd,
        shell=False,
        additional_env=GazeboRosPaths.get_env(),
    )

    platforms = platforms.replace(" ", "").split(",")
    state_publishers = []
    for platform in platforms:
        print(f"Platform {platform}")
        namespace, xacro_path = "", ""

        if platform.lower() in ["panther", "lynx"]:
            namespace = platform.lower()
            xacro_path = get_file_path(
                "rcdt_gazebo", ["urdf", "husarion"], f"{platform.lower()}.urdf.xacro"
            )
            robot_description = get_robot_description(xacro_path)
            state_publishers.append(
                Node(
                    package="robot_state_publisher",
                    executable="robot_state_publisher",
                    name="state_publisher",
                    namespace=namespace,
                    parameters=[
                        robot_description,
                        {"frame_prefix": ""},
                        {"publish_frequency": 1000.0},
                    ],
                )
            )

    bridge_topics.append("/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock")
    bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=bridge_topics,
    )

    spawn_platforms = Node(
        package="rcdt_gazebo",
        executable="spawn_platforms.py",
        parameters=[
            {
                "platforms": ",".join(platforms),  # todo make this nicer
                "positions": positions,
                "orientations": orientations,
                "parents": parents,
                "parent_links": parent_links,
            },
        ],
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
        *[Register.on_start(node, context) for node in state_publishers],
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
            load_gazebo_ui_arg.declaration,
            world_arg.declaration,
            platforms_arg.declaration,
            positions_arg.declaration,
            orientations_arg.declaration,
            bridge_topics_arg.declaration,
            OpaqueFunction(function=launch_setup),
        ]
    )
