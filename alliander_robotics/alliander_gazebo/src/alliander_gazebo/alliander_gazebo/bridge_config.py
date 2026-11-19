# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

from typing import Literal, TypeVar

import yaml
from alliander_utilities.config_objects import (
    GPS,
    IMU,
    Beamagine,
    Camera,
    Lidar,
    Platform,
    ThermalCamera,
    Vehicle,
)

T = TypeVar("T", bound=Platform)


class BridgeConfig:
    """Class to create a bridge configuration for ROS and Gazebo topics."""

    def __init__(self, config_file: str):
        """Initialize.

        Args:
            config_file (str): The path of the configuration file.
        """
        self.config_file = config_file
        self.config = []
        self.image_topics = []
        self.image_remaps = []

    def bridge_clock(self) -> None:
        """Bridge the /clock topic."""
        self.config.append(
            {
                "ros_topic_name": "/clock",
                "gz_topic_name": "/clock",
                "ros_type_name": "rosgraph_msgs/msg/Clock",
                "gz_type_name": "gz.msgs.Clock",
                "direction": "GZ_TO_ROS",
            }
        )

    def bridge_battery(self, ns: str) -> None:
        """Bridge the battery topic.

        Args:
            ns (str): The namespace.
        """
        self.config.append(
            {
                "ros_topic_name": f"/{ns}/battery/battery_status",
                "gz_topic_name": f"/model/{ns}/battery/{ns}/battery/state",
                "ros_type_name": "sensor_msgs/msg/BatteryState",
                "gz_type_name": "gz.msgs.BatteryState",
                "direction": "GZ_TO_ROS",
            }
        )

    def bridge_lidar(self, ns: str) -> None:
        """Bridge the lidar topic.

        Args:
            ns (str): The namespace.
        """
        self.config.append(
            {
                "ros_topic_name": f"/{ns}/scan/points",
                "gz_topic_name": f"/{ns}/scan/points",
                "ros_type_name": "sensor_msgs/msg/PointCloud2",
                "gz_type_name": "gz.msgs.PointCloudPacked",
                "direction": "GZ_TO_ROS",
            }
        )

    def bridge_camera(self, ns: str, camera_type: Literal["color", "depth"]) -> None:
        """Bridge the camera topics using ros_gz_image bridge to have compressed image topics.

        Args:
            ns (str): The namespace.
            camera_type (Literal["color", "depth"]): The type of camera.
        """
        topic = f"/{ns}/image" if camera_type == "color" else f"/{ns}/depth_image"
        remap = f"/{ns}/{camera_type}/image"
        sub_topics = ["compressed", "compressedDepth", "theora", "zstd"]
        self.image_topics.append(topic)
        self.image_remaps.append((topic, remap))
        for sub_topic in sub_topics:
            self.image_remaps.append((f"{topic}/{sub_topic}", f"{remap}/{sub_topic}"))

    def bridge_camera_info(
        self, ns: str, camera_type: Literal["color", "depth"]
    ) -> None:
        """Bridge the camera info topic.

        Args:
            ns (str): The namespace.
            camera_type (Literal["color", "depth"]): The type of camera.
        """
        self.config.append(
            {
                "ros_topic_name": f"/{ns}/{camera_type}/camera_info",
                "gz_topic_name": f"/{ns}/camera_info",
                "ros_type_name": "sensor_msgs/msg/CameraInfo",
                "gz_type_name": "gz.msgs.CameraInfo",
                "direction": "GZ_TO_ROS",
            }
        )

    def bridge_camera_points(self, platform: Platform) -> None:
        """Bridge the camera points topic for supported platforms.

        Args:
            platform (Platform): The platform containing the camera.
        """
        ns = platform.namespace
        match platform.name:
            case "zed":
                points_frame_id = f"/{ns}/{ns}_left_camera_frame"
            case "realsense":
                points_frame_id = f"/{ns}/camera_color_frame"
            case _:
                points_frame_id = None
        if points_frame_id:
            self.config.append(
                {
                    "ros_topic_name": f"/{ns}/points",
                    "gz_topic_name": f"/{ns}/points",
                    "ros_type_name": "sensor_msgs/msg/PointCloud2",
                    "gz_type_name": "gz.msgs.PointCloudPacked",
                    "frame_id": points_frame_id,
                    "direction": "GZ_TO_ROS",
                }
            )

    def bridge_gps(self, ns: str) -> None:
        """Bridge the GPS topic.

        Args:
            ns (str): The namespace.
        """
        self.config.append(
            {
                "ros_topic_name": f"/{ns}/gps/fix_raw",
                "gz_topic_name": f"/{ns}/gps/fix_raw",
                "ros_type_name": "sensor_msgs/msg/NavSatFix",
                "gz_type_name": "gz.msgs.NavSat",
                "direction": "GZ_TO_ROS",
            }
        )

    def bridge_thermal_camera(self, ns: str) -> None:
        """Bridge the thermal camera topic.

        Args:
            ns (str): The namespace.
        """
        self.config.append(
            {
                "ros_topic_name": f"/{ns}/thermal/image",
                "gz_topic_name": f"/{ns}/thermal/image",
                "ros_type_name": "sensor_msgs/msg/Image",
                "gz_type_name": "gz.msgs.Image",
                "direction": "GZ_TO_ROS",
            }
        )

    def bridge_imu(self, ns: str) -> None:
        """Bridge the IMU topic.

        Args:
            ns (str): The namespace.
        """
        self.config.append(
            {
                "ros_topic_name": f"/{ns}/imu/data",
                "gz_topic_name": f"/{ns}/imu/data",
                "ros_type_name": "sensor_msgs/msg/Imu",
                "gz_type_name": "gz.msgs.IMU",
                "direction": "GZ_TO_ROS",
            }
        )

    def create_bridge_config(self, platforms: list[T]) -> None:
        """Create the bridge configuration for the given platforms.

        Args:
            platforms (list[T]): The list of platforms in the simulation.
        """
        self.bridge_clock()

        for platform in platforms:
            ns = platform.namespace
            if isinstance(platform, Vehicle):
                self.bridge_battery(ns)
            if isinstance(platform, Lidar):
                self.bridge_lidar(ns)
            if isinstance(platform, Camera):
                self.bridge_camera(ns, "color")
                self.bridge_camera_info(ns, "color")
                if not platform.simulate_high_resolution:
                    self.bridge_camera(ns, "depth")
                    self.bridge_camera_info(ns, "depth")
                    self.bridge_camera_points(platform)
            if isinstance(platform, ThermalCamera):
                self.bridge_thermal_camera(ns)
            if isinstance(platform, Beamagine):
                self.bridge_camera(ns, "color")
                self.bridge_camera_info(ns, "color")
                self.bridge_thermal_camera(ns)
                self.bridge_lidar(ns)
            if isinstance(platform, GPS):
                self.bridge_gps(ns)
            if isinstance(platform, IMU):
                self.bridge_imu(ns)

        with open(self.config_file, "w", encoding="utf-8") as outfile:
            yaml.dump(self.config, outfile, sort_keys=False)
