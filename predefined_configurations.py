# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

# ruff: noqa: PLR0904

from __future__ import annotations

from typing import Callable, Dict

from alliander_core.src.alliander_utilities.alliander_utilities.config_objects import (
    GPS,
    Arm,
    Camera,
    Lidar,
    Platform,
    PlatformList,
    SimulatorConfig,
    Vehicle,
    VisualizationConfig,
    link,
)

ConfigurationFunction = Callable[["PredefinedConfigurations"], None]

PLATFORM_CONFIGS: Dict[str, ConfigurationFunction] = {}


class PredefinedConfigurations:
    """Provides access to a collection of predefined platform configurations."""

    def __init__(self):
        """Initialize the PredefinedConfigurations class."""
        self.plat_conf = PlatformList()
        self.sim_conf = SimulatorConfig()
        self.viz_conf = VisualizationConfig()

    def apply_configuration(self, config_name: str) -> None:
        """Instantiates the provided platform configuration.

        Args:
            config_name (str): Name of the platform configuration.

        Raises:
            ValueError: If the provided configuration is not a valid option.
        """
        if config_name not in PLATFORM_CONFIGS:
            raise ValueError(f"Unknown configuration: {config_name}")

        self.plat_conf.platforms.clear()
        PLATFORM_CONFIGS[config_name](self)

    @staticmethod
    def get_names() -> list:
        """Get a list of all registered platform configuration names.

        Returns:
            list: List of all platform configuration options.
        """
        return list(PLATFORM_CONFIGS.keys())

    @staticmethod
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
    def config_empty(self) -> None:  # noqa: D102
        self.plat_conf.platforms = []

    @register_configuration("axis")
    def config_axis(self) -> None:  # noqa: D102
        self.plat_conf.platforms = [Platform("axis")]

    @register_configuration("gps")
    def config_gps(self) -> None:  # noqa: D102
        self.plat_conf.platforms = [GPS("gps", (0, 0, 0.5), ip_address="10.15.20.202")]

    @register_configuration("ouster")
    def config_ouster(self) -> None:  # noqa: D102
        self.plat_conf.platforms = [Lidar("ouster", (0, 0, 0.5))]

    @register_configuration("velodyne")
    def config_velodyne(self) -> None:  # noqa: D102
        self.plat_conf.platforms = [Lidar("velodyne", (0, 0, 0.5))]

    @register_configuration("realsense")
    def config_realsense(self) -> None:  # noqa: D102
        self.plat_conf.platforms = [Camera("realsense", (0, 0, 0.5))]

    @register_configuration("zed")
    def config_zed(self) -> None:  # noqa: D102
        self.plat_conf.platforms = [Camera("zed", (0, 0, 0.5), namespace="zed")]

    # Franka:
    @register_configuration("franka")
    def config_franka(self) -> None:  # noqa: D102
        arm = Arm("franka", gripper=True, moveit=True)

        self.plat_conf.platforms = [arm]
        self.viz_conf.gui = True

    @register_configuration("franka_rviz_motion_planning")
    def config_franka_rviz_motion_planning(self) -> None:  # noqa: D102
        arm = Arm("franka", gripper=True, moveit=True)
        arm.moveit_config.load_rviz_motion_planning_plugin = True

        self.plat_conf.platforms = [arm]
        self.viz_conf.gui = True

    @register_configuration("franka_realsense")
    def config_franka_realsense(self) -> None:  # noqa: D102
        arm = Arm("franka", moveit=True)
        camera = Camera("realsense", (0.05, 0, 0), (0, -90, 180))

        link(arm, camera)
        self.plat_conf.platforms = [arm, camera]

    # Panther:
    @register_configuration("panther")
    def config_panther(self) -> None:  # noqa: D102
        self.plat_conf.platforms = [
            Vehicle("panther", (0, 0, 0.2), namespace="panther")
        ]

    @register_configuration("panther_realsense")
    def config_panther_realsense(self) -> None:  # noqa: D102
        vehicle = Vehicle("panther", (0, 0, 0.2))
        camera = Camera("realsense", (0.18, 0, 0.2))

        link(vehicle, camera)
        self.plat_conf.platforms = [vehicle, camera]

    @register_configuration("panther_zed")
    def config_panther_zed(self) -> None:  # noqa: D102
        vehicle = Vehicle("panther", (0, 0, 0.2))
        camera = Camera("zed", (0, 0, 0.5))

        link(vehicle, camera)
        self.plat_conf.platforms = [vehicle, camera]

    @register_configuration("panther_velodyne")
    def config_panther_velodyne(self) -> None:  # noqa: D102
        vehicle = Vehicle("panther", (0, 0, 0.2))
        lidar = Lidar(
            "velodyne",
            position=(0.125, 0.185, 0.20),
            orientation=(0.0, 0.0, 45.0),
            ip_address="10.15.20.5",
        )

        link(vehicle, lidar)
        self.plat_conf.platforms = [vehicle, lidar]

    @register_configuration("panther_ouster")
    def config_panther_ouster(self) -> None:  # noqa: D102
        vehicle = Vehicle("panther", (0, 0, 0.2))
        lidar = Lidar("ouster", (0.13, -0.13, 0.35))

        link(vehicle, lidar)
        self.plat_conf.platforms = [vehicle, lidar]

    @register_configuration("panther_gps")
    def config_panther_gps(self) -> None:  # noqa: D102
        vehicle = Vehicle("panther", (0, 0, 0.2))
        gps = GPS("gps", position=(-0.08, -0.25, 0.2), orientation=(0, 0, -90))

        link(vehicle, gps)
        self.plat_conf.platforms = [vehicle, gps]
        self.sim_conf.world = "map_5.940906_51.966960"

    @register_configuration("panther_collision_monitor")
    def config_panther_collision_monitor(self) -> None:  # noqa: D102
        vehicle = Vehicle("panther", (0, 0, 0.2))
        vehicle.nav2_config.collision_monitor = True
        lidar = Lidar(
            "velodyne",
            position=(0.125, 0.185, 0.20),
            orientation=(0.0, 0.0, 45.0),
            ip_address="10.15.20.5",
        )

        link(vehicle, lidar)
        self.plat_conf.platforms = [vehicle, lidar]

    @register_configuration("panther_slam")
    def config_panther_slam(self) -> None:  # noqa: D102
        vehicle = Vehicle("panther", (0, 0, 0.2))
        vehicle.nav2_config.slam = True
        lidar = Lidar(
            "velodyne",
            position=(0.125, 0.185, 0.20),
            orientation=(0.0, 0.0, 45.0),
            ip_address="10.15.20.5",
        )

        link(vehicle, lidar)
        self.plat_conf.platforms = [vehicle, lidar]

    @register_configuration("panther_lidar_navigation")
    def config_panther_lidar_navigation(self) -> None:  # noqa: D102
        vehicle = Vehicle("panther", (0, 0, 0.2))
        vehicle.nav2_config.navigation = True
        lidar = Lidar(
            "velodyne",
            position=(0.125, 0.185, 0.20),
            orientation=(0.0, 0.0, 45.0),
            ip_address="10.15.20.5",
        )

        link(vehicle, lidar)
        self.plat_conf.platforms = [vehicle, lidar]
        self.sim_conf.world = "walls.sdf"

    @register_configuration("panther_gps_navigation")
    def config_panther_gps_navigation(self) -> None:  # noqa: D102
        vehicle = Vehicle("panther", (0, 0, 0.2), (0, 0, 45))
        vehicle.nav2_config.controller = "mppi"
        vehicle.nav2_config.navigation = True
        vehicle.nav2_config.gps = True
        vehicle.nav2_config.window_size = 50
        lidar = Lidar(
            "velodyne",
            position=(0.125, 0.185, 0.2),
            orientation=(0, 0, 45),
            ip_address="10.15.20.5",
        )
        gps = GPS("gps", position=(-0.08, -0.25, 0.2), orientation=(0, 0, -90))
        camera = Camera("realsense", (0.18, 0, 0.2))

        link(vehicle, lidar)
        link(vehicle, gps)
        link(vehicle, camera)
        self.plat_conf.platforms = [vehicle, lidar, gps, camera]
        self.viz_conf.gui = True
        self.sim_conf.world = "map_5.954036_51.977320"

    # Lynx:
    @register_configuration("lynx")
    def config_lynx(self) -> None:  # noqa: D102
        self.plat_conf.platforms = [Vehicle("lynx", (0, 0, 0.13), namespace="lynx")]

    @register_configuration("lynx_ouster")
    def config_lynx_ouster(self) -> None:  # noqa: D102
        vehicle = Vehicle("lynx", (0, 0, 0.13))
        lidar = Lidar("ouster", (0.1, -0.1, 0.25))

        link(vehicle, lidar)
        self.plat_conf.platforms = [vehicle, lidar]

    # Mobile Manipulators:
    @register_configuration("mm")
    def config_mm(self) -> None:  # noqa: D102
        vehicle = Vehicle("panther", (0, 0, 0.2))
        arm = Arm("franka", (0, 0, 0.14), gripper=True, moveit=True)

        link(vehicle, arm)
        self.plat_conf.platforms = [vehicle, arm]

    @register_configuration("mm_velodyne")
    def config_mm_velodyne(self) -> None:  # noqa: D102
        vehicle = Vehicle("panther", (0, 0, 0.2))
        vehicle.nav2_config.navigation = True
        arm = Arm("franka", (0, 0, 0.14), gripper=True, moveit=True)
        lidar = Lidar(
            "velodyne",
            position=(0.125, 0.185, 0.20),
            orientation=(0.0, 0.0, 45.0),
            ip_address="10.15.20.5",
        )

        link(vehicle, arm)
        link(vehicle, lidar)
        self.plat_conf.platforms = [vehicle, arm, lidar]

    # Multiple non-connected platforms:
    @register_configuration("panther_and_franka")
    def config_panther_and_franka(self) -> None:  # noqa: D102
        vehicle = Vehicle("panther", (0, -0.5, 0.2))
        arm = Arm("franka", (0, 0.5, 0))
        self.plat_conf.platforms = [vehicle, arm]
