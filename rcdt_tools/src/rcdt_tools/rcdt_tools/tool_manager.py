# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

from rcdt_utilities.config_objects import Platform, ToolsConfig

from rcdt_tools.rviz import Rviz
from rcdt_tools.vizanti import Vizanti


class ApplyConfigurations:
    def __init__(self, config: ToolsConfig):
        Rviz.set_fixed_frame("map")

        for platform in config.platforms:
            Rviz.add_platform_model(platform.namespace)
            match platform.platform_type:
                case "Arm":
                    self.add_arm(platform)
                case "Vehicle":
                    self.add_vehicle(platform)
                case "Lidar":
                    self.add_lidar(platform)
                case "Camera":
                    self.add_depth_camera(platform)
                case "GPS":
                    self.add_gps(platform)

        if config.rviz:
            Rviz.create_rviz_file()

        if config.vizanti:
            Vizanti.create_config_file()

    @staticmethod
    def add_arm(platform: Platform):
        ns = platform.namespace
        # if use_moveit:
        #     Rviz.moveit_namespaces.append(ns)
        #     Rviz.add_motion_planning_plugin(ns)
        #     Rviz.add_planning_scene(ns)
        #     Rviz.add_robot_state(ns)
        #     Rviz.add_trajectory(ns)

    @staticmethod
    def add_vehicle(platform: Platform):
        ns = platform.namespace
        Vizanti.add_platform_model(platform.namespace)
        Vizanti.add_button("Trigger", f"/{ns}/hardware/e_stop_trigger")
        Vizanti.add_button("Reset", f"/{ns}/hardware/e_stop_reset")
        Vizanti.add_button(
            "Estop Status", f"/{ns}/hardware/e_stop", "std_msgs/msg/Bool"
        )
        Vizanti.add_button("Stop", f"/{ns}/waypoint_follower_controller/stop")
        Vizanti.add_initial_pose()
        Vizanti.add_goal_pose()
        Vizanti.add_waypoints(ns)
        Vizanti.add_map("global_costmap", f"/{ns}/global_costmap/costmap")
        Vizanti.add_path(f"/{ns}/plan")

    @staticmethod
    def add_lidar(platform: Platform):
        Rviz.add_laser_scan(platform.namespace)

    @staticmethod
    def add_depth_camera(platform: Platform):
        Rviz.add_image(f"/{platform.namespace}/color/image_raw")
        Rviz.add_image(f"/{platform.namespace}/depth/image_rect_raw")
        Rviz.add_depth_cloud(
            f"/{platform.namespace}/color/image_raw",
            f"/{platform.namespace}/depth/image_rect_raw",
        )

    @staticmethod
    def add_gps(platform: Platform):
        Rviz.add_satellite(f"/{platform.namespace}/gps/fix")
