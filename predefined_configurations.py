# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import Callable, Dict

from rcdt_core.src.rcdt_utilities.rcdt_utilities.config_objects import (
    GPS,
    Arm,
    Camera,
    Lidar,
    Platform,
    Vehicle,
    link,
)

ConfigurationFunction = Callable[[], None]

PLATFORM_CONFIGS: Dict[str, ConfigurationFunction] = {}


class PredefinedConfigurations:
    """Provides access to a collection of predefined platform configurations."""

    platforms: dict[str, "Platform"] = {}
    world: str = "empty.sdf"
    gazebo_ui: bool = False
    rviz: bool = True
    vizanti: bool = False
    rcdt_gui: bool = False

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
    platform = Platform("axis")

    PredefinedConfigurations.platforms[platform.namespace] = platform


@register_configuration("gps")
def config_gps() -> None:  # noqa: D103
    gps = GPS("gps", (0, 0, 0.5), ip_address="10.15.20.202")

    PredefinedConfigurations.platforms[gps.namespace] = gps


@register_configuration("ouster")
def config_ouster() -> None:  # noqa: D103
    lidar = Lidar("ouster", (0, 0, 0.5))

    PredefinedConfigurations.platforms[lidar.namespace] = lidar


@register_configuration("velodyne")
def config_velodyne() -> None:  # noqa: D103
    lidar = Lidar("velodyne", (0, 0, 0.5))

    PredefinedConfigurations.platforms[lidar.namespace] = lidar


@register_configuration("realsense")
def config_realsense() -> None:  # noqa: D103
    camera = Camera("realsense", (0, 0, 0.5))

    PredefinedConfigurations.platforms[camera.namespace] = camera


@register_configuration("zed")
def config_zed() -> None:  # noqa: D103
    camera = Camera("zed", (0, 0, 0.5), namespace="zed")

    PredefinedConfigurations.platforms[camera.namespace] = camera


# Franka:
@register_configuration("franka")
def config_franka() -> None:  # noqa: D103
    arm = Arm("franka", gripper=True, moveit=True)

    PredefinedConfigurations.rcdt_gui = True
    PredefinedConfigurations.platforms[arm.namespace] = arm


@register_configuration("franka_rviz_motion_planning")
def config_franka_rviz_motion_planning() -> None:  # noqa: D103
    arm = Arm("franka", gripper=True, moveit=True)
    arm.moveit_config.load_rviz_motion_planning_plugin = True

    PredefinedConfigurations.rcdt_gui = True
    PredefinedConfigurations.platforms[arm.namespace] = arm


@register_configuration("franka_realsense")
def config_franka_realsense() -> None:  # noqa: D103
    arm = Arm("franka", moveit=True)
    camera = Camera("realsense", (0.05, 0, 0), (0, -90, 180))
    link(arm, camera)

    PredefinedConfigurations.platforms[arm.namespace] = arm
    PredefinedConfigurations.platforms[camera.namespace] = camera


# Panther:
@register_configuration("panther")
def config_panther() -> None:  # noqa: D103
    vehicle = Vehicle("panther", (0, 0, 0.2), namespace="panther")

    PredefinedConfigurations.platforms[vehicle.namespace] = vehicle


@register_configuration("panther_realsense")
def config_panther_realsense() -> None:  # noqa: D103
    vehicle = Vehicle("panther", (0, 0, 0.2))
    camera = Camera("realsense", (0, 0, 0.2))
    link(vehicle, camera)

    PredefinedConfigurations.platforms[vehicle.namespace] = vehicle
    PredefinedConfigurations.platforms[camera.namespace] = camera


@register_configuration("panther_zed")
def config_panther_zed() -> None:  # noqa: D103
    vehicle = Vehicle("panther", (0, 0, 0.2))
    camera = Camera("zed", (0, 0, 0.5))
    link(vehicle, camera)

    PredefinedConfigurations.platforms[vehicle.namespace] = vehicle
    PredefinedConfigurations.platforms[camera.namespace] = camera


@register_configuration("panther_velodyne")
def config_panther_velodyne() -> None:  # noqa: D103
    vehicle = Vehicle("panther", (0, 0, 0.2))
    lidar = Lidar("velodyne", (0.13, -0.13, 0.35), ip_address="10.15.20.5")
    link(vehicle, lidar)

    PredefinedConfigurations.platforms[vehicle.namespace] = vehicle
    PredefinedConfigurations.platforms[lidar.namespace] = lidar


@register_configuration("panther_ouster")
def config_panther_ouster() -> None:  # noqa: D103
    vehicle = Vehicle("panther", (0, 0, 0.2))
    lidar = Lidar("ouster", (0.13, -0.13, 0.35))
    link(vehicle, lidar)

    PredefinedConfigurations.platforms[vehicle.namespace] = vehicle
    PredefinedConfigurations.platforms[lidar.namespace] = lidar


@register_configuration("panther_gps")
def config_panther_gps() -> None:  # noqa: D103
    PredefinedConfigurations.world = "map_5.940906_51.966960"
    vehicle = Vehicle("panther", (0, 0, 0.2))
    gps = GPS("gps", (0, 0, 0.2))
    link(vehicle, gps)

    PredefinedConfigurations.platforms[vehicle.namespace] = vehicle
    PredefinedConfigurations.platforms[gps.namespace] = gps


@register_configuration("panther_collision_monitor")
def config_panther_collision_monitor() -> None:  # noqa: D103
    vehicle = Vehicle("panther", (0, 0, 0.2))
    vehicle.nav2_config.collision_monitor = True
    lidar = Lidar("velodyne", (0.13, -0.13, 0.35))
    link(vehicle, lidar)

    PredefinedConfigurations.platforms[vehicle.namespace] = vehicle
    PredefinedConfigurations.platforms[lidar.namespace] = lidar


@register_configuration("panther_slam")
def config_panther_slam() -> None:  # noqa: D103
    vehicle = Vehicle("panther", (0, 0, 0.2))
    vehicle.nav2_config.slam = True
    lidar = Lidar("velodyne", (0.13, -0.13, 0.35))
    link(vehicle, lidar)

    PredefinedConfigurations.platforms[vehicle.namespace] = vehicle
    PredefinedConfigurations.platforms[lidar.namespace] = lidar


@register_configuration("panther_lidar_navigation")
def config_panther_lidar_navigation() -> None:  # noqa: D103
    PredefinedConfigurations.world = "walls.sdf"
    vehicle = Vehicle("panther", (0, 0, 0.2))
    vehicle.nav2_config.navigation = True
    lidar = Lidar("velodyne", (0.13, -0.13, 0.35))
    link(vehicle, lidar)

    PredefinedConfigurations.platforms[vehicle.namespace] = vehicle
    PredefinedConfigurations.platforms[lidar.namespace] = lidar


@register_configuration("panther_gps_navigation")
def config_panther_gps_navigation() -> None:  # noqa: D103
    PredefinedConfigurations.world = "map_5.940906_51.966960"
    PredefinedConfigurations.rcdt_gui = True
    vehicle = Vehicle("panther", (0, 0, 0.2))
    vehicle.nav2_config.navigation = True
    vehicle.nav2_config.gps = True
    lidar = Lidar("velodyne", (0.13, -0.13, 0.35))
    gps = GPS("gps", (0, 0, 0.2))
    link(vehicle, lidar)
    link(vehicle, gps)

    PredefinedConfigurations.platforms[vehicle.namespace] = vehicle
    PredefinedConfigurations.platforms[lidar.namespace] = lidar
    PredefinedConfigurations.platforms[gps.namespace] = gps


# # Lynx:
@register_configuration("lynx")
def config_lynx() -> None:  # noqa: D103
    vehicle = Vehicle("lynx", (0, 0, 0.13), namespace="lynx")

    PredefinedConfigurations.platforms[vehicle.namespace] = vehicle


@register_configuration("lynx_ouster")
def config_lynx_ouster() -> None:  # noqa: D103
    vehicle = Vehicle("lynx", (0, 0, 0.13))
    lidar = Lidar("ouster", (0.1, -0.1, 0.25))
    link(vehicle, lidar)

    PredefinedConfigurations.platforms[vehicle.namespace] = vehicle
    PredefinedConfigurations.platforms[lidar.namespace] = lidar


# Mobile Manipulators:
@register_configuration("mm")
def config_mm() -> None:  # noqa: D103
    vehicle = Vehicle("panther", (0, 0, 0.2))
    arm = Arm("franka", (0, 0, 0.14), gripper=True, moveit=True)
    link(vehicle, arm)

    PredefinedConfigurations.platforms[vehicle.namespace] = vehicle
    PredefinedConfigurations.platforms[arm.namespace] = arm


@register_configuration("mm_velodyne")
def config_mm_velodyne() -> None:  # noqa: D103
    vehicle = Vehicle("panther", (0, 0, 0.2))
    vehicle.nav2_config.navigation = True
    arm = Arm("franka", (0, 0, 0.14), gripper=True, moveit=True)
    lidar = Lidar("velodyne", (0.13, -0.13, 0.35))
    link(vehicle, arm)
    link(vehicle, lidar)

    PredefinedConfigurations.platforms[vehicle.namespace] = vehicle
    PredefinedConfigurations.platforms[arm.namespace] = arm
    PredefinedConfigurations.platforms[lidar.namespace] = lidar


# Multiple non-connected platforms:
@register_configuration("panther_and_franka")
def config_panther_and_franka() -> None:  # noqa: D103
    vehicle = Vehicle("panther", (0, -0.5, 0.2))
    arm = Arm("franka", (0, 0.5, 0))

    PredefinedConfigurations.platforms[vehicle.namespace] = vehicle
    PredefinedConfigurations.platforms[arm.namespace] = arm
