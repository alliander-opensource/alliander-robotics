# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0
import subprocess

from alliander_utilities.config_objects import (
    GPS,
    Arm,
    Camera,
    Lidar,
    PlatformList,
    Vehicle,
    VisualizationConfig,
)

from alliander_visualization.rviz import Rviz
from alliander_visualization.vizanti import Vizanti


class ApplyConfigurations:
    """Apply configurations to visualization tools like RViz and Vizanti.

    Attributes:
        rviz_parameters (list): list of parameters to set for Rviz.
    """

    rviz_parameters: list = []

    def __init__(self, config: VisualizationConfig, platform_list: PlatformList):
        """Initialize.

        Args:
            config (VisualizationConfig): configuration for Visualization tool -- list of platforms and boolean flags.
            platform_list (PlatformList): a list of all platforms required for the selected configuration.

        Raises:
            NotImplementedError: if platform.platform_type does not match any of the implemented types.
        """
        Rviz.set_fixed_frame("map")

        for platform in platform_list.platforms:
            Rviz.add_platform_model(platform.namespace)
            match platform.platform_type:
                case "Arm":
                    self.add_arm(Arm.from_str(platform.to_str()))
                case "Vehicle":
                    self.add_vehicle(Vehicle.from_str(platform.to_str()))
                case "Lidar":
                    self.add_lidar(Lidar.from_str(platform.to_str()))
                case "Camera":
                    self.add_depth_camera(Camera.from_str(platform.to_str()))
                case "GPS":
                    self.add_gps(GPS.from_str(platform.to_str()))
                case _:
                    raise NotImplementedError(
                        f"Configuration for platform {type(platform).__name__} is not implemented."
                    )

        if config.rviz:
            Rviz.create_rviz_file()

        if config.vizanti:
            Vizanti.create_config_file()

    # TODO: refactor this
    @staticmethod
    def add_description(
        namespace: str, semantic: bool = False, kinematic: bool = False
    ) -> None:
        """Obtain robot description parameters and add them to RViz parameters.

        Args:
            namespace (str): namespace for tobot description.
            semantic (bool): whether it is a semantic robot description or not.
            kinematic (bool): whether it is a kinematic robot description or not.
        """
        if kinematic:
            ApplyConfigurations.rviz_parameters.append(
                {
                    f"{namespace}_robot_description_kinematics": {
                        "arm": {
                            "kinematics_solver": "kdl_kinematics_plugin/KDLKinematicsPlugin"
                        }
                    }
                }
            )
            return

        description = "robot_description_semantic" if semantic else "robot_description"
        cmd = f"ros2 param get /{namespace}/move_group {description} --hide-type"
        proc = subprocess.run([cmd], shell=True, check=False, capture_output=True)
        stdout = proc.stdout.decode("utf-8").rstrip()
        ApplyConfigurations.rviz_parameters.append(
            {f"{namespace}_{description}": stdout}
        )

    @staticmethod
    def add_arm(platform: Arm) -> None:
        """Add arm configurations to RViz and Vizanti.

        Args:
            platform (Arm): The arm platform configuration.
        """
        ns = platform.namespace
        if platform.moveit:
            ApplyConfigurations.add_description(ns)
            ApplyConfigurations.add_description(ns, semantic=True)
            ApplyConfigurations.add_description(ns, kinematic=True)
            Rviz.add_planning_scene(ns)
            Rviz.add_robot_state(ns)
            Rviz.add_arm_trajectory(ns)
            Rviz.add_markers()
            if platform.moveit_config.load_rviz_motion_planning_plugin:
                Rviz.add_motion_planning_plugin(ns)

    @staticmethod
    def add_vehicle(platform: Vehicle) -> None:
        """Add vehicle configurations to RViz and Vizanti.

        Args:
            platform (Vehicle): The vehicle platform configuration.
        """
        ns = platform.namespace
        nav2 = platform.nav2_config
        Vizanti.add_platform_model(ns)

        if (nav2.navigation or nav2.slam) and not nav2.gps:
            Rviz.add_map(f"/{ns}/map", "map")

        if nav2.navigation:
            Rviz.add_map(f"/{ns}/global_costmap/costmap")
            Rviz.add_map(f"/{ns}/local_costmap/costmap", "map", 0.3)
            Rviz.add_odometry(f"/{ns}/odometry/global")
            Rviz.add_path(f"/{ns}/plan")
            Rviz.add_vehicle_trajectory(f"/{ns}/optimal_trajectory")
            Vizanti.add_button("Stop", f"/{ns}/waypoint_follower_controller/stop")
            Vizanti.add_initial_pose()
            Vizanti.add_goal_pose()
            Vizanti.add_waypoints(ns)
            Vizanti.add_map("global_costmap", f"/{ns}/global_costmap/costmap")
            Vizanti.add_path(f"/{ns}/plan")

        if nav2.gps:
            Rviz.set_grid_size(nav2.window_size)
            Rviz.set_grid_frame(f"/{ns}/base_footprint")

        if nav2.collision_monitor:
            Rviz.add_polygon(f"/{ns}/polygon_slower")
            Rviz.add_polygon(f"/{ns}/velocity_polygon_stop")

    @staticmethod
    def add_lidar(platform: Lidar) -> None:
        """Add lidar configurations to RViz and Vizanti.

        Args:
            platform (Lidar): The lidar platform configuration.
        """
        Rviz.add_laser_scan(platform.namespace)
        Rviz.add_point_cloud(platform.namespace)

    @staticmethod
    def add_depth_camera(platform: Camera) -> None:
        """Add depth camera configurations to RViz and Vizanti.

        Args:
            platform (Camera): The camera platform configuration.
        """
        Rviz.add_image(f"/{platform.namespace}/color/image_raw")
        Rviz.add_image(f"/{platform.namespace}/depth/image_rect_raw")
        Rviz.add_depth_cloud(
            f"/{platform.namespace}/color/image_raw",
            f"/{platform.namespace}/depth/image_rect_raw",
        )

    @staticmethod
    def add_gps(platform: GPS) -> None:
        """Add GPS configurations to RViz and Vizanti.

        Args:
            platform (GPS): The GPS platform configuration.
        """
        Rviz.add_satellite(f"/{platform.namespace}/gps/fix")
