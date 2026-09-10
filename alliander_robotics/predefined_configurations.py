# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

# ruff: noqa: PLR0904

from __future__ import annotations

from typing import Callable, Dict

from alliander_robotics.alliander_core.src.alliander_utilities.alliander_utilities.config_objects import (
    GPS,
    IMU,
    Apriltag,
    Arm,
    Beamagine,
    Camera,
    Gripper,
    Lidar,
    Lift,
    NtripConfig,
    Platform,
    PlatformList,
    SimulatorConfig,
    ThermalCamera,
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

    # Apriltag:
    @register_configuration("apriltag")
    def config_apriltag(self) -> None:  # noqa: D102
        self.plat_conf.platforms = [Apriltag("apriltag", (0, 0, 0.5))]

    # Sensors:
    @register_configuration("")
    def config_empty(self) -> None:  # noqa: D102
        self.plat_conf.platforms = []

    @register_configuration("axis")
    def config_axis(self) -> None:  # noqa: D102
        self.plat_conf.platforms = [Platform("axis")]

    @register_configuration("ublox")
    def config_gps(self) -> None:  # noqa: D102
        ntrip = NtripConfig()
        gps = GPS(
            "ublox",
            (0, 0, 0.5),
            namespace="ublox",
            ntrip_config=ntrip,
        )
        self.plat_conf.platforms = [gps]

    @register_configuration("dual_ublox")
    def config_dual_gps(self) -> None:  # noqa: D102
        ntrip = NtripConfig()
        gps_base = GPS(
            "ublox",
            (0.5, 0.5, 0.5),
            namespace="ublox_base",
            operation_mode="mb_base",
            ntrip_config=ntrip,
            usb_device="BASE",
        )
        gps_rover = GPS(
            "ublox",
            (-0.5, -0.5, 0.5),
            namespace="ublox_rover",
            operation_mode="mb_rover",
            ntrip_config=ntrip,
            usb_device="ROVER",
        )
        self.plat_conf.platforms = [gps_base, gps_rover]

    @register_configuration("ouster")
    def config_ouster(self) -> None:  # noqa: D102
        self.plat_conf.platforms = [Lidar("ouster", (0, 0, 0.5))]

    @register_configuration("velodyne")
    def config_velodyne(self) -> None:  # noqa: D102
        self.plat_conf.platforms = [Lidar("velodyne", (0, 0, 0.5))]

    @register_configuration("realsense")
    def config_realsense(self) -> None:  # noqa: D102
        self.plat_conf.platforms = [Camera("realsense", (0, 0, 0.5))]

    @register_configuration("xsens")
    def config_xsens(self) -> None:  # noqa: D102
        self.plat_conf.platforms = [IMU("xsens", (0, 0, 0.5))]

    @register_configuration("zed")
    def config_zed(self) -> None:  # noqa: D102
        self.plat_conf.platforms = [Camera("zed", (0, 0, 0.5), namespace="zed")]

    @register_configuration("seekthermal")
    def config_seekthermal(self) -> None:  # noqa: D102
        self.plat_conf.platforms = [
            ThermalCamera(
                "seekthermal", (0, -3, 0.5), (0, 0, 90), namespace="seekthermal"
            )
        ]

        self.sim_conf.world = "thermal_camera.sdf"

    @register_configuration("beamagine")
    def config_beamagine(self) -> None:  # noqa: D102
        self.plat_conf.platforms = [
            Beamagine("beamagine", (0, 0, 0.5), namespace="beamagine")
        ]
        self.sim_conf.world = "walls.sdf"

    # Ewellix:
    @register_configuration("ewellix")
    def config_ewellix(self) -> None:  # noqa: D102
        self.plat_conf.platforms = [Lift("ewellix")]

    @register_configuration("ewellix_franka")
    def config_ewellix_franka(self) -> None:  # noqa: D102
        lift = Lift("ewellix")
        arm = Arm("franka")

        link(lift, arm)
        self.plat_conf.platforms = [lift, arm]

    # Grippers:
    @register_configuration("robotiq")
    def config_robotiq(self) -> None:  # noqa: D102
        self.plat_conf.platforms = [Gripper("robotiq", (0, 0, 0.5))]

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

    # UR:
    @register_configuration("ur")
    def config_ur(self) -> None:  # noqa: D102
        arm = Arm("ur", moveit=True, ip_address="172.16.0.2")

        self.plat_conf.platforms = [arm]
        self.viz_conf.gui = True

    @register_configuration("ur_rviz_motion_planning")
    def config_ur_rviz_motion_planning(self) -> None:  # noqa: D102
        arm = Arm("ur", moveit=True, ip_address="172.16.0.2")
        arm.moveit_config.load_rviz_motion_planning_plugin = True

        self.plat_conf.platforms = [arm]

    @register_configuration("ur_realsense")
    def config_ur_realsense(self) -> None:  # noqa: D102
        arm = Arm("ur", moveit=True)
        camera = Camera("realsense", (0.05, 0, 0), (0, -90, 180))

        link(arm, camera)
        self.plat_conf.platforms = [arm, camera]

    @register_configuration("ur_robotiq")
    def config_ur_robotiq(self) -> None:  # noqa: D102
        arm = Arm("ur", moveit=True)
        gripper = Gripper("robotiq", (0, 0, 0.05), (0, 180, 0))

        link(arm, gripper)
        self.plat_conf.platforms = [arm, gripper]

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
        self.sim_conf.world = "walls.sdf"

    @register_configuration("panther_zed")
    def config_panther_zed(self) -> None:  # noqa: D102
        vehicle = Vehicle("panther", (0, 0, 0.2))
        camera = Camera("zed", (0.08, 0, 0.4), orientation=(0, 10, 0))

        link(vehicle, camera)
        self.plat_conf.platforms = [vehicle, camera]

    @register_configuration("panther_seekthermal")
    def config_panther_seekthermal(self) -> None:  # noqa: D102
        vehicle = Vehicle("panther", (0, -3, 0.2), (0, 0, 90))
        thermal_camera = ThermalCamera("seekthermal", (0, 0, 0.2))

        link(vehicle, thermal_camera)
        self.plat_conf.platforms = [vehicle, thermal_camera]
        self.sim_conf.world = "thermal_camera.sdf"

    @register_configuration("panther_velodyne")
    def config_panther_velodyne(self) -> None:  # noqa: D102
        vehicle = Vehicle("panther", (0, 0, 0.2))
        lidar = Lidar(
            "velodyne",
            position=(0.13, 0.17, 0.18),
            orientation=(0, 0, 0),
            ip_address="10.15.20.5",
        )

        link(vehicle, lidar)
        self.plat_conf.platforms = [vehicle, lidar]

    @register_configuration("panther_xsens")
    def config_panther_xsens(self) -> None:  # noqa: D102
        vehicle = Vehicle("panther", (0, 0, 0.2))
        imu = IMU("xsens", position=(0.16, -0.09, 0.155), orientation=(90, 0, -90))

        link(vehicle, imu)
        self.plat_conf.platforms = [vehicle, imu]

    @register_configuration("panther_ouster")
    def config_panther_ouster(self) -> None:  # noqa: D102
        vehicle = Vehicle("panther", (0, 0, 0.2))
        lidar = Lidar("ouster", (0.13, -0.13, 0.35))

        link(vehicle, lidar)
        self.plat_conf.platforms = [vehicle, lidar]

    @register_configuration("panther_beamagine")
    def config_panther_beamagine(self) -> None:  # noqa: D102
        vehicle = Vehicle("panther", (0, 0, 0.2))
        beamagine = Beamagine("beamagine", (0, 0, 0.3))

        link(vehicle, beamagine)
        self.plat_conf.platforms = [vehicle, beamagine]
        self.sim_conf.world = "walls.sdf"

    @register_configuration("panther_ublox")
    def config_panther_ublox(self) -> None:  # noqa: D102
        vehicle = Vehicle("panther", (0, 0, 0.2))
        ntrip = NtripConfig()
        gps = GPS(
            "ublox",
            (-0.21, -0.2, 0.19),
            namespace="ublox",
            operation_mode="rover",
            ntrip_config=ntrip,
            usb_device="PANTHER",
        )
        link(vehicle, gps)
        self.plat_conf.platforms = [vehicle, gps]
        self.sim_conf.world = "map_5.940906_51.966960"

    @register_configuration("panther_collision_monitor")
    def config_panther_collision_monitor(self) -> None:  # noqa: D102
        vehicle = Vehicle("panther", (0, 0, 0.2))
        vehicle.nav2_config.collision_monitor = True
        vehicle.nav2_config.navigation = True
        lidar = Lidar(
            "velodyne",
            position=(0.13, 0.17, 0.18),
            orientation=(0, 0, 0),
            ip_address="10.15.20.5",
        )

        link(vehicle, lidar)
        self.plat_conf.platforms = [vehicle, lidar]

    @register_configuration("panther_slam")
    def config_panther_slam(self) -> None:  # noqa: D102
        vehicle = Vehicle("panther", (0, 0, 0.2))
        vehicle.nav2_config.slam = True
        vehicle.nav2_config.navigation = True
        vehicle.nav2_config.window_size = 20
        lidar = Lidar(
            "velodyne",
            position=(0.13, 0.17, 0.18),
            orientation=(0, 0, 0),
            ip_address="10.15.20.5",
        )

        link(vehicle, lidar)
        self.plat_conf.platforms = [vehicle, lidar]
        self.sim_conf.world = "walls.sdf"

    @register_configuration("panther_lidar_navigation")
    def config_panther_lidar_navigation(self) -> None:  # noqa: D102
        vehicle = Vehicle("panther", (0, 0, 0.2))
        vehicle.nav2_config.navigation = True
        lidar = Lidar(
            "velodyne",
            position=(0.13, 0.17, 0.18),
            orientation=(0, 0, 0),
            ip_address="10.15.20.5",
        )

        link(vehicle, lidar)
        self.plat_conf.platforms = [vehicle, lidar]
        self.sim_conf.world = "walls.sdf"

    @register_configuration("panther_outdoor_navigation")
    def config_panther_outdoor_navigation(self) -> None:  # noqa: D102
        vehicle = Vehicle("panther", (0, 0, 0.2), (0, 0, 45))
        vehicle.nav2_config.controller = "mppi"
        vehicle.nav2_config.navigation = True
        vehicle.nav2_config.gps = True
        vehicle.nav2_config.window_size = 150

        lidar = Lidar(
            "velodyne",
            position=(0.13, 0.17, 0.18),
            orientation=(0, 0, 0),
            ip_address="10.15.20.5",
        )

        ntrip = NtripConfig()
        gps = GPS(
            "ublox",
            (-0.21, -0.2, 0.19),
            namespace="ublox",
            operation_mode="rover",
            ntrip_config=ntrip,
            usb_device="PANTHER",
        )
        imu = IMU("xsens", position=(0.16, -0.09, 0.155), orientation=(90, 0, -90))

        link(vehicle, lidar)
        link(vehicle, gps)
        link(vehicle, imu)
        self.plat_conf.platforms = [vehicle, lidar, gps, imu]
        self.viz_conf.gui = True
        self.sim_conf.world = "map_5.954036_51.977320"

    @register_configuration("panther_outdoor_navigation_zed")
    def config_panther_outdoor_navigation_zed(self) -> None:  # noqa: D102
        vehicle = Vehicle("panther", (0, 0, 0.2), (0, 0, 45))
        vehicle.nav2_config.controller = "mppi"
        vehicle.nav2_config.navigation = True
        vehicle.nav2_config.gps = True
        vehicle.nav2_config.window_size = 150

        lidar = Lidar(
            "velodyne",
            position=(0.13, 0.17, 0.18),
            orientation=(0, 0, 0),
            ip_address="10.15.20.5",
        )

        ntrip = NtripConfig()
        gps = GPS(
            "ublox",
            (-0.21, -0.2, 0.19),
            namespace="ublox",
            operation_mode="rover",
            ntrip_config=ntrip,
            usb_device="PANTHER",
        )
        imu = IMU("xsens", position=(0.16, -0.09, 0.155), orientation=(90, 0, -90))
        camera = Camera("zed", (0.08, 0, 0.4), orientation=(0, 10, 0))

        link(vehicle, lidar)
        link(vehicle, gps)
        link(vehicle, imu)
        link(vehicle, camera)
        self.plat_conf.platforms = [vehicle, lidar, gps, imu, camera]
        self.viz_conf.gui = True
        self.sim_conf.world = "map_5.954036_51.977320"

    # Lynx:
    @register_configuration("lynx")
    def config_lynx(self) -> None:  # noqa: D102
        self.plat_conf.platforms = [Vehicle("lynx", (0, 0, 0.13), namespace="lynx")]

    @register_configuration("lynx_realsense")
    def config_lynx_realsense(self) -> None:  # noqa: D102
        vehicle = Vehicle("lynx", (0, 0, 0.13), namespace="lynx")
        camera = Camera("realsense", (0.15, 0, 0.23))

        link(vehicle, camera)
        self.plat_conf.platforms = [vehicle, camera]

    @register_configuration("lynx_ouster")
    def config_lynx_ouster(self) -> None:  # noqa: D102
        vehicle = Vehicle("lynx", (0, 0, 0.13))
        lidar = Lidar("ouster", (0.1, -0.1, 0.25))

        link(vehicle, lidar)
        self.plat_conf.platforms = [vehicle, lidar]

    @register_configuration("lynx_outdoor_navigation")
    def config_lynx_gps_navigation(self) -> None:  # noqa: D102
        vehicle = Vehicle("lynx", (0, 0, 0.13))
        vehicle.nav2_config.navigation = True
        vehicle.nav2_config.gps = True
        vehicle.nav2_config.window_size = 50

        lidar = Lidar("ouster", (0.06, 0.0, 0.25))
        ntrip = NtripConfig()
        gps = GPS(
            "ublox",
            (-0.21, 0.2, 0.19),
            namespace="gps",
            operation_mode="rover",
            ntrip_config=ntrip,
            usb_device="LYNX",
        )
        imu = IMU("xsens", position=(-0.28, 0.04, 0.25), orientation=(0, 0, 180))

        link(vehicle, lidar)
        link(vehicle, gps)
        link(vehicle, imu)
        self.plat_conf.platforms = [vehicle, lidar, gps, imu]
        self.viz_conf.gui = True
        self.sim_conf.world = "map_5.940906_51.966960"

    @register_configuration("lynx_lidar_navigation")
    def config_lynx_lidar_navigation(self) -> None:  # noqa: D102
        vehicle = Vehicle("lynx", (0, 0, 0.2))
        vehicle.nav2_config.navigation = True
        vehicle.nav2_config.controller = "mppi"
        lidar = Lidar("ouster", (0.06, 0.0, 0.25))
        imu = IMU("xsens", position=(-0.28, 0.04, 0.25), orientation=(0, 0, 180))

        link(vehicle, lidar)
        link(vehicle, imu)
        self.plat_conf.platforms = [vehicle, lidar, imu]
        self.sim_conf.world = "walls.sdf"

    # Mobile Manipulators:
    @register_configuration("mm_pf")
    def config_pf(self) -> None:  # noqa: D102
        vehicle = Vehicle("panther", (0, 0, 0.2))
        arm = Arm("franka", (0, 0, 0.14), gripper=True, moveit=True)

        link(vehicle, arm)
        self.plat_conf.platforms = [vehicle, arm]

    @register_configuration("mm_pu")
    def config_pu(self) -> None:  # noqa: D102
        vehicle = Vehicle("panther", (0, 0, 0.2))
        arm = Arm("ur", (0, 0, 0.14), moveit=True)

        link(vehicle, arm)
        self.plat_conf.platforms = [vehicle, arm]

    @register_configuration("mm_ewellix")
    def config_mm_ewellix(self) -> None:  # noqa: D102
        vehicle = Vehicle("panther", (0, 0, 0.2))
        lift = Lift("ewellix", (0, 0, 0.14))
        arm = Arm("franka")

        link(vehicle, lift)
        link(lift, arm)
        self.plat_conf.platforms = [vehicle, lift, arm]

    @register_configuration("mm_pfv")
    def config_pfv(self) -> None:  # noqa: D102
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

    @register_configuration("mm_puv")
    def config_puv(self) -> None:  # noqa: D102
        vehicle = Vehicle("panther", (0, 0, 0.2))
        vehicle.nav2_config.navigation = True
        arm = Arm("ur", (0, 0, 0.14), moveit=True)
        lidar = Lidar("velodyne", (0.13, -0.13, 0.35))

        link(vehicle, arm)
        link(vehicle, lidar)
        self.plat_conf.platforms = [vehicle, arm, lidar]

    # Multiple non-connected platforms:
    @register_configuration("panther_and_franka")
    def config_panther_and_franka(self) -> None:  # noqa: D102
        vehicle = Vehicle("panther", (0, -0.5, 0.2))
        arm = Arm("franka", (0, 0.5, 0))
        self.plat_conf.platforms = [vehicle, arm]

    # Demos
    @register_configuration("franka_arm_wave_demo")
    def config_franka_arm_wave_demo(self) -> None:  # noqa: D102
        arm = Arm(
            "franka",
            gripper=True,
            moveit=True,
            movement="wave",
            ip_address="172.16.0.2",
        )

        self.plat_conf.platforms = [arm]
        self.viz_conf.gui = True

    @register_configuration("ur_arm_wave_demo")
    def config_ur_arm_wave_demo(self) -> None:  # noqa: D102
        arm = Arm(
            "ur",
            gripper=False,
            moveit=True,
            movement="wave",
            ip_address="172.16.0.2",
        )

        self.plat_conf.platforms = [arm]
        self.viz_conf.gui = True

    @register_configuration("mm_arm_wave_demo")
    def config_mm_arm_wave_demo(self) -> None:  # noqa: D102
        vehicle = Vehicle("panther", (0, 0, 0.2))
        arm = Arm(
            "franka",
            (0, 0, 0.14),
            gripper=True,
            moveit=True,
            movement="wave",
            ip_address="10.15.20.4",
        )

        link(vehicle, arm)
        self.plat_conf.platforms = [vehicle, arm]

    @register_configuration("lynx_indoor_demo")
    def config_lynx_indoor_demo(self) -> None:  # noqa: D102
        vehicle = Vehicle("lynx", (0, 0, 0.2))
        vehicle.nav2_config.navigation = True
        vehicle.nav2_config.controller = "mppi"
        lidar = Lidar("ouster", (0.06, 0.0, 0.25))
        imu = IMU("xsens", position=(-0.28, 0.04, 0.25), orientation=(0, 0, 180))
        camera = Camera("realsense", (0.30, 0, 0.18))

        link(vehicle, lidar)
        link(vehicle, imu)
        link(vehicle, camera)
        self.plat_conf.platforms = [vehicle, lidar, imu, camera]
        self.sim_conf.world = "walls.sdf"
        self.viz_conf.gui = True
