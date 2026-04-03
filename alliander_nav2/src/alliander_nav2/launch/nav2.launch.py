# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

from alliander_utilities.adapted_yaml import AdaptedYaml
from alliander_utilities.config_objects import Vehicle
from alliander_utilities.launch_argument import LaunchArgument
from alliander_utilities.launch_utils import SKIP
from alliander_utilities.register import Register
from alliander_utilities.ros_utils import get_file_path
from launch import LaunchContext, LaunchDescription
from launch.actions import ExecuteProcess, OpaqueFunction
from launch_ros.actions import LifecycleNode, Node, SetParameter, SetRemap

platform_arg = LaunchArgument("platform_config", "")


def launch_setup(context: LaunchContext) -> list:  # noqa: PLR0915
    """The launch setup.

    Args:
        context (LaunchContext): The launch context.

    Returns:
        list: The actions to start.

    Raises:
        ValueError: If GPS is enabled but no GPS is child of vehicle.
    """
    vehicle_config = Vehicle.from_str(platform_arg.string_value(context))
    namespace_vehicle = vehicle_config.namespace
    nav2 = vehicle_config.nav2_config

    # Extract lidar and gps namespaces from childs. The first found will be used:
    namespace_gps = ""
    namespace_lidar = ""
    for child in vehicle_config.childs:
        if child.platform_type == "Lidar" and not namespace_lidar:
            namespace_lidar = child.namespace
        if child.platform_type == "GPS" and not namespace_gps:
            namespace_gps = child.namespace

    # Define configuration:
    lifecycle_nodes_names = []
    use_map_localization = True
    plugins = ["static_layer", "obstacle_layer", "inflation_layer"]

    if nav2.collision_monitor:
        lifecycle_nodes_names.append("collision_monitor")
    if nav2.slam:
        lifecycle_nodes_names.append("slam_toolbox")
        use_map_localization = False
    if nav2.gps:
        if not namespace_gps:
            raise ValueError("Namespace for GPS must be provided when using GPS.")
        use_map_localization = False
    if nav2.navigation:
        if use_map_localization:
            lifecycle_nodes_names.extend(
                [
                    "map_server",
                    "amcl",
                ]
            )
        else:
            plugins.remove("static_layer")
        lifecycle_nodes_names.extend(
            [
                "controller_server",
                "planner_server",
                "behavior_server",
                "bt_navigator",
                "waypoint_follower",
            ]
        )

    # Define parameters:
    slam_params = AdaptedYaml(
        get_file_path("alliander_nav2", ["config"], "slam_params.yaml"),
        {
            "odom_frame": f"{namespace_vehicle}/odom",
            "base_frame": f"{namespace_vehicle}/base_footprint",
            "scan_topic": f"/{namespace_lidar}/scan",
        },
        root_key=namespace_vehicle,
    )

    amcl_params = AdaptedYaml(
        get_file_path("alliander_nav2", ["config", "nav2"], "amcl.yaml"),
        {
            "base_frame_id": f"{namespace_vehicle}/base_footprint",
            "odom_frame_id": f"{namespace_vehicle}/odom",
            "scan_topic": f"/{namespace_lidar}/scan",
        },
        root_key=namespace_vehicle,
    )

    local_costmap_params = AdaptedYaml(
        get_file_path("alliander_nav2", ["config", "nav2"], "local_costmap.yaml"),
        {
            "global_frame": f"{namespace_vehicle}/odom",
            "robot_base_frame": f"{namespace_vehicle}/base_footprint",
            "rolling_window": nav2.gps,
            "plugins": plugins,
        },
        root_key=namespace_vehicle,
    )

    global_costmap_params = AdaptedYaml(
        get_file_path("alliander_nav2", ["config", "nav2"], "global_costmap.yaml"),
        {
            "robot_base_frame": f"{namespace_vehicle}/base_footprint",
            "rolling_window": nav2.gps,
            "width": nav2.window_size,
            "height": nav2.window_size,
            "plugins": plugins,
            "obstacle_layer": {
                "scan": {
                    "topic": f"/{namespace_lidar}/scan",
                    "obstacle_max_range": float(nav2.window_size),
                    "raytrace_max_range": float(nav2.window_size),
                }
            },
        },
        root_key=namespace_vehicle,
    )

    controller_server_params = AdaptedYaml(
        get_file_path("alliander_nav2", ["config", "nav2"], "controller_server.yaml"),
        {"odom_topic": f"/{namespace_vehicle}/odom"},
        root_key=namespace_vehicle,
    )

    behavior_server_params = AdaptedYaml(
        get_file_path("alliander_nav2", ["config", "nav2"], "behavior_server.yaml"),
        {
            "local_frame": f"{namespace_vehicle}/odom",
            "robot_base_frame": f"{namespace_vehicle}/base_footprint",
        },
        root_key=namespace_vehicle,
    )

    follow_path_params = AdaptedYaml(
        get_file_path(
            "alliander_nav2",
            ["config", "nav2", "controllers"],
            f"{nav2.controller}.yaml",
        ),
        {},
        root_key=namespace_vehicle,
    )

    bt_navigator_params = AdaptedYaml(
        get_file_path("alliander_nav2", ["config", "nav2"], "bt_navigator.yaml"),
        {
            "default_nav_to_pose_bt_xml": get_file_path(
                "alliander_nav2", ["config", "nav2"], "behavior_tree.xml"
            ),
            "robot_base_frame": f"{namespace_vehicle}/base_footprint",
            "odom_topic": f"/{namespace_vehicle}/odom",
        },
        root_key=namespace_vehicle,
    )

    planner_server_params = AdaptedYaml(
        get_file_path("alliander_nav2", ["config", "nav2"], "planner_server.yaml"),
        {},
        root_key=namespace_vehicle,
    )

    collision_monitor_params = AdaptedYaml(
        get_file_path("alliander_nav2", ["config", "nav2"], "collision_monitor.yaml"),
        {
            "base_frame_id": f"{namespace_vehicle}/base_footprint",
            "odom_frame_id": f"{namespace_vehicle}/odom",
            "cmd_vel_in_topic": f"/{namespace_vehicle}/cmd_vel_raw",
            "cmd_vel_out_topic": f"/{namespace_vehicle}/cmd_vel",
            "scan": {
                "topic": f"/{namespace_lidar}/scan",
            },
        },
        root_key=namespace_vehicle,
    )

    # Define lifecycle nodes:
    all_lifecycle_nodes = {}

    all_lifecycle_nodes["collision_monitor"] = LifecycleNode(
        package="nav2_collision_monitor",
        executable="collision_monitor",
        name="collision_monitor",
        parameters=[collision_monitor_params.file],
        namespace=namespace_vehicle,
    )

    all_lifecycle_nodes["slam_toolbox"] = LifecycleNode(
        package="slam_toolbox",
        executable="async_slam_toolbox_node",
        name="slam_toolbox",
        parameters=[
            slam_params.file,
            {
                "use_lifecycle_manager": True,
            },
        ],
        namespace=namespace_vehicle,
        remappings=[("/map", f"/{namespace_vehicle}/map")],
    )

    all_lifecycle_nodes["map_server"] = LifecycleNode(
        package="nav2_map_server",
        executable="map_server",
        name="map_server",
        parameters=[
            {
                "yaml_filename": get_file_path(
                    "alliander_nav2", ["config", "maps"], f"{nav2.map}.yaml"
                ),
                "topic_name": f"/{namespace_vehicle}/map",
            }
        ],
        namespace=namespace_vehicle,
    )

    all_lifecycle_nodes["amcl"] = LifecycleNode(
        package="nav2_amcl",
        executable="amcl",
        name="amcl",
        parameters=[amcl_params.file],
        namespace=namespace_vehicle,
        remappings=[(f"/{namespace_vehicle}/initialpose", "/initialpose")],
    )

    all_lifecycle_nodes["controller_server"] = LifecycleNode(
        package="nav2_controller",
        executable="controller_server",
        name="controller_server",
        parameters=[
            local_costmap_params.file,
            controller_server_params.file,
            follow_path_params.file,
        ],
        namespace=namespace_vehicle,
    )

    all_lifecycle_nodes["planner_server"] = LifecycleNode(
        package="nav2_planner",
        executable="planner_server",
        name="planner_server",
        parameters=[
            global_costmap_params.file,
            planner_server_params.file,
        ],
        namespace=namespace_vehicle,
    )

    all_lifecycle_nodes["behavior_server"] = LifecycleNode(
        package="nav2_behaviors",
        executable="behavior_server",
        name="behavior_server",
        parameters=[behavior_server_params.file],
        namespace=namespace_vehicle,
    )

    all_lifecycle_nodes["bt_navigator"] = LifecycleNode(
        package="nav2_bt_navigator",
        executable="bt_navigator",
        name="bt_navigator",
        parameters=[bt_navigator_params.file],
        namespace=namespace_vehicle,
    )

    remappings = []
    if nav2.gps:
        remappings.append(("/gps/fix", f"/{namespace_gps}/fix"))
        remappings.append(("/fromLL", f"/{namespace_gps}/fromLL"))

    all_lifecycle_nodes["waypoint_follower"] = LifecycleNode(
        package="nav2_waypoint_follower",
        executable="waypoint_follower",
        name="waypoint_follower",
        namespace=namespace_vehicle,
        remappings=remappings,
    )

    lifecycle_manager = Node(
        package="nav2_lifecycle_manager",
        executable="lifecycle_manager",
        name="lifecycle_manager_navigation",
        parameters=[{"autostart": True}, {"node_names": lifecycle_nodes_names}],
        namespace=namespace_vehicle,
    )

    nav2_manager = Node(
        package="alliander_nav2",
        executable="nav2_manager.py",
        namespace=namespace_vehicle,
        remappings=remappings,
    )

    pub_topic = (
        f"/{namespace_vehicle}/cmd_vel"
        if not nav2.collision_monitor
        else f"/{namespace_vehicle}/cmd_vel_raw"
    )

    register_lifecycle_nodes = []
    for node_name in lifecycle_nodes_names:
        register_lifecycle_nodes.append(all_lifecycle_nodes[node_name])

    sleep = ExecuteProcess(
        cmd=[
            "sleep",
            "15",
        ],
        shell=False,
    )

    return [
        SetParameter(name="use_sim_time", value=vehicle_config.simulation),
        SetRemap(src="/cmd_vel", dst=pub_topic),
        Register.on_exit(sleep, context),
        *[Register.on_start(node, context) for node in register_lifecycle_nodes],
        Register.on_log(lifecycle_manager, "Managed nodes are active", context),
        Register.on_log(nav2_manager, "Controller is ready.", context)
        if nav2.navigation
        else SKIP,
    ]


def generate_launch_description() -> LaunchDescription:
    """Generate the launch description for the navigation stack.

    Returns:
        LaunchDescription: The launch description containing the actions to be executed.
    """
    return LaunchDescription(
        [
            platform_arg.declaration,
            OpaqueFunction(function=launch_setup),
        ]
    )
