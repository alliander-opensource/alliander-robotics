# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

from typing import Callable, Dict

from rcdt_launch.environment_configuration import EnvironmentConfiguration
from rcdt_launch.platforms.arm import Arm
from rcdt_launch.platforms.camera import Camera
from rcdt_launch.platforms.gps import GPS
from rcdt_launch.platforms.lidar import Lidar
from rcdt_launch.platforms.platform import Platform
from rcdt_launch.platforms.vehicle import Vehicle
from rcdt_launch.rviz import Rviz

ConfigurationFunction = Callable[[], None]

PLATFORM_CONFIGS: Dict[str, ConfigurationFunction] = {}


class PredefinedConfigurations:
    """Provides access to a collection of predefined platform configurations."""

    @staticmethod
    def apply_configuration(config_name: str) -> None:
        """Instantiates the provided platform configuration.

        Args:
            config_name (str): Name of the platform configuration.

        Raises:
            ValueError: If the provided configuration is not a valid option.
        """
        if config_name not in PLATFORM_CONFIGS:
            raise ValueError(f"Unknown configuration: {config_name}")

        PLATFORM_CONFIGS[config_name]()

    @staticmethod
    def get_names() -> list:
        """Get a list of all registered platform configuration names.

        Returns:
            list: List of all platform configuration options.
        """
        return list(PLATFORM_CONFIGS.keys())


def register_configuration(
    name: str,
) -> Callable[[ConfigurationFunction], ConfigurationFunction]:
    """Decorator to register a configuration by name.

    Args:
        name (str): The identifyer of the configuration.

    Returns:
        Callable[[ConfigurationFunction], ConfigurationFunction]:
            A decorator that registers the function under the provided name.
    """

    def wrapper(fn: ConfigurationFunction) -> ConfigurationFunction:
        PLATFORM_CONFIGS[name] = fn
        return fn

    return wrapper


# Sensors:
@register_configuration("")
def config_empty() -> None:  # noqa: D103
    pass


@register_configuration("axis")
def config_axis() -> None:  # noqa: D103
    Platform("axis", [0, 0, 0])


@register_configuration("gps")
def config_gps() -> None:  # noqa: D103
    GPS("nmea", [0, 0, 0.5], ip_address="10.15.20.202")


@register_configuration("ouster")
def config_ouster() -> None:  # noqa: D103
    Lidar("ouster", [0, 0, 0.5])


@register_configuration("velodyne")
def config_velodyne() -> None:  # noqa: D103
    Lidar("velodyne", [0, 0, 0.5])


@register_configuration("realsense")
def config_realsense() -> None:  # noqa: D103
    Camera("realsense", [0, 0, 0.5])


@register_configuration("zed")
def config_zed() -> None:  # noqa: D103
    Camera("zed", [0, 0, 0.5], namespace="zed")


# Franka:
@register_configuration("franka")
def config_franka() -> None:  # noqa: D103
    if not EnvironmentConfiguration.simulation:
        Rviz.load_motion_planning_plugin = True
    Arm("franka", [0, 0, 0], gripper=True, moveit=True, ip_address="172.16.0.2")


@register_configuration("franka_realsense")
def config_franka_realsense() -> None:  # noqa: D103
    arm = Arm("franka", [0, 0, 0], moveit=True)
    Camera("realsense", [0.05, 0, 0], [0, -90, 180], parent=arm)


@register_configuration("franka_double")
def config_franka_double() -> None:  # noqa: D103
    EnvironmentConfiguration.use_joystick = False
    Rviz.load_motion_planning_plugin = True
    Arm("franka", [1.0, 0, 0], gripper=True, moveit=True)
    Arm("franka", [-1.0, 0, 0], gripper=True, moveit=True)


@register_configuration("franka_planning")
def config_franka_planning() -> None:  # noqa: D103
    EnvironmentConfiguration.world = "table_with_1_brick.sdf"
    Rviz.add_markers()
    Rviz.load_robot_state = True
    Rviz.load_trajectory = True
    Rviz.load_planning_scene = True
    arm = Arm("franka", [0, 0, 0], moveit=True)
    Camera("realsense", [0.05, 0, 0], [0, -90, 180], parent=arm)


# Panther:
@register_configuration("panther")
def config_panther() -> None:  # noqa: D103
    Vehicle("panther", [0, 0, 0.2], namespace="panther")


@register_configuration("panther_realsense")
def config_panther_realsense() -> None:  # noqa: D103
    panther = Vehicle("panther", [0, 0, 0.2])
    Camera("realsense", [0, 0, 0.2], parent=panther)


@register_configuration("panther_zed")
def config_panther_zed() -> None:  # noqa: D103
    panther = Vehicle("panther", [0, 0, 0.2])
    Camera("zed", [0, 0, 0.5], parent=panther)


@register_configuration("panther_velodyne")
def config_panther_velodyne() -> None:  # noqa: D103
    panther = Vehicle("panther", [0, 0, 0.2])
    Lidar("velodyne", [0.13, -0.13, 0.35], parent=panther)


@register_configuration("panther_ouster")
def config_panther_ouster() -> None:  # noqa: D103
    panther = Vehicle("panther", [0, 0, 0.2])
    Lidar("ouster", [0.13, -0.13, 0.35], parent=panther)


@register_configuration("panther_collision_monitor")
def config_panther_collision_monitor() -> None:  # noqa: D103
    panther = Vehicle("panther", [0, 0, 0.2], collision_monitor=True)
    Lidar("velodyne", [0.13, -0.13, 0.35], parent=panther)


@register_configuration("panther_slam")
def config_panther_slam() -> None:  # noqa: D103
    panther = Vehicle("panther", [0, 0, 0.2], slam=True)
    Lidar("velodyne", [0.13, -0.13, 0.35], parent=panther)


@register_configuration("panther_lidar_navigation")
def config_panther_lidar_navigation() -> None:  # noqa: D103
    panther = Vehicle("panther", [0, 0, 0.2], navigation=True)
    Lidar("velodyne", [0.13, -0.13, 0.35], parent=panther)


@register_configuration("panther_gps_navigation")
def config_panther_gps() -> None:  # noqa: D103
    EnvironmentConfiguration.world = "map_5.940906_51.966960"
    EnvironmentConfiguration.use_vizanti = True
    panther = Vehicle(
        "panther", [0, 0, 0.2], navigation=True, use_gps=True, window_size=50
    )
    Lidar("velodyne", [0.13, -0.13, 0.35], parent=panther)
    GPS("nmea", [0, 0, 0.2], parent=panther)


# Mobile Manipulators:
@register_configuration("mm")
def config_mm() -> None:  # noqa: D103
    panther = Vehicle("panther", [0, 0, 0.2])
    Arm("franka", [0, 0, 0.14], gripper=True, parent=panther, moveit=True)


@register_configuration("mm_velodyne")
def config_mm_velodyne() -> None:  # noqa: D103
    panther = Vehicle("panther", [0, 0, 0.2], navigation=True)
    Arm("franka", [0, 0, 0.14], gripper=True, parent=panther, moveit=True)
    Lidar("velodyne", [0.13, -0.13, 0.35], parent=panther)


@register_configuration("mm_ouster")
def config_mm_ouster() -> None:  # noqa: D103
    panther = Vehicle("panther", [0, 0, 0.2], navigation=True)
    Arm("franka", [0, 0, 0.14], gripper=True, parent=panther, moveit=True)
    Lidar("ouster", [0.13, -0.13, 0.35], parent=panther)


@register_configuration("mm_gps")
def config_mm_gps() -> None:  # noqa: D103
    EnvironmentConfiguration.world = "map_5.940906_51.966960"
    panther = Vehicle(
        "panther", [0, 0, 0.2], navigation=True, use_gps=True, window_size=50
    )
    Arm("franka", [0, 0, 0.14], gripper=True, parent=panther, moveit=True)
    Lidar("velodyne", [0.13, -0.13, 0.35], parent=panther)
    GPS("nmea", [0, 0, 0.2], parent=panther)


# Multiple non-connected platforms:
@register_configuration("panther_and_franka")
def config_panther_and_franka() -> None:  # noqa: D103
    Vehicle("panther", [0, -0.5, 0.2])
    Arm("franka", [0, 0.5, 0])
