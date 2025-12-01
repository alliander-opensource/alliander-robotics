# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

from launch import LaunchContext, LaunchDescription
from launch.actions import OpaqueFunction
from launch_ros.actions import Node, SetParameter
from rcdt_launch.environment_configuration import EnvironmentConfiguration
from rcdt_launch.predefined_configurations import PredefinedConfigurations
from rcdt_launch.rviz import Rviz
from rcdt_launch.vizanti import Vizanti
from rcdt_utilities import launch_utils
from rcdt_utilities.launch_argument import LaunchArgument
from rcdt_utilities.register import Register, RegisteredLaunchDescription
from rcdt_utilities.ros_utils import get_file_path

use_sim_arg = LaunchArgument("simulation", True, [True, False])
load_gazebo_ui_arg = LaunchArgument("load_gazebo_ui", False, [True, False])
use_rviz_arg = LaunchArgument("rviz", True, [True, False])
use_vizanti_arg = LaunchArgument("vizanti", False, [True, False])
configuration_arg = LaunchArgument(
    "configuration",
    "",
    PredefinedConfigurations.get_names(),
)


def launch_setup(context: LaunchContext) -> list:
    """Setup the launch description for the Panther robot.

    Args:
        context (LaunchContext): The launch context.

    Returns:
        list: A list of actions to be executed in the launch description.

    Raises:
        RuntimeError: If no platforms are specified.
    """
    config_name = configuration_arg.string_value(context)
    load_gazebo_ui = load_gazebo_ui_arg.bool_value(context)
    use_rviz = use_rviz_arg.bool_value(context)
    EnvironmentConfiguration.use_vizanti = use_vizanti_arg.bool_value(context)
    EnvironmentConfiguration.simulation = use_sim_arg.bool_value(context)
    Rviz.load_motion_planning_plugin = False
    Rviz.load_point_cloud = False

    PredefinedConfigurations.apply_configuration(config_name)

    if EnvironmentConfiguration.platforms == []:
        raise RuntimeError("No platforms specified. Please specify a platform.")
    launch_utils.order_platforms()

    state_publishers = launch_utils.create_state_publishers()
    gazebo = launch_utils.create_gazebo_launch(load_gazebo_ui)
    hardware_interfaces = launch_utils.create_hardware_interfaces()
    map_links = launch_utils.create_map_links()
    parent_links = launch_utils.create_parent_links()
    controllers = launch_utils.create_controllers()
    launch_descriptions = launch_utils.create_launch_descriptions()
    joystick_nodes = (
        launch_utils.create_joystick_nodes()
        if EnvironmentConfiguration.use_joystick
        else []
    )

    utilities = RegisteredLaunchDescription(
        get_file_path("rcdt_utilities", ["launch"], "utils.launch.py")
    )

    Rviz.set_fixed_frame("map")
    Rviz.create_rviz_file()
    rviz = RegisteredLaunchDescription(
        get_file_path("rcdt_utilities", ["launch"], "rviz.launch.py")
    )

    Vizanti.create_config_file()
    vizanti = RegisteredLaunchDescription(
        get_file_path("rcdt_panther", ["launch"], "vizanti.launch.py")
    )

    platforms_dict = {
        platform.namespace: type(platform).__name__
        for platform in EnvironmentConfiguration.platforms
    }
    rcdt_gui = Node(
        package="rcdt_utilities",
        executable="rcdt_gui.py",
        parameters=[{"platforms": str(platforms_dict)}],
    )
    start_rcdt_gui = not set(platforms_dict.values()).isdisjoint(["Arm", "Vehicle"])
    return [
        SetParameter(name="use_sim_time", value=EnvironmentConfiguration.simulation),
        Register.on_start(rcdt_gui, context) if start_rcdt_gui else launch_utils.SKIP,
        Register.group(rviz, context) if use_rviz else launch_utils.SKIP,
        *[Register.on_start(node, context) for node in state_publishers],
        Register.group(gazebo, context)
        if EnvironmentConfiguration.simulation
        else launch_utils.SKIP,
        *[Register.group(group, context) for group in hardware_interfaces],
        *[Register.on_start(node, context) for node in map_links],
        *[Register.on_start(node, context) for node in parent_links],
        *[Register.group(node, context) for node in controllers],
        Register.group(utilities, context),
        *[Register.on_start(node, context) for node in joystick_nodes],
        *[Register.group(group, context) for group in launch_descriptions],
        Register.group(vizanti, context)
        if EnvironmentConfiguration.use_vizanti
        else launch_utils.SKIP,
    ]


def generate_launch_description() -> LaunchDescription:
    """Generate the launch description for the Panther robot.

    Returns:
        LaunchDescription: The launch description for the Panther robot.
    """
    return LaunchDescription(
        [
            use_sim_arg.declaration,
            load_gazebo_ui_arg.declaration,
            use_rviz_arg.declaration,
            use_vizanti_arg.declaration,
            configuration_arg.declaration,
            OpaqueFunction(function=launch_setup),
        ]
    )
