# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

from typing import TypeVar

import yaml
from alliander_utilities.config_objects import Platform

T = TypeVar("T", bound=Platform)


class BridgeConfig:
    """Class to create a bridge configuration for ROS and Gazebo topics."""

    def __init__(self, config_file: str):
        """Initialize.

        Args:
            config_file (str): The path of the configuration file.
        """
        self.config_file = config_file
        self.image_topics = []
        self.image_remaps = []

    def create_bridge_config(self, platforms: list[T]) -> None:
        """Create the bridge configuration for the given platforms.

        Args:
            platforms (list[T]): The list of platforms in the simulation.
        """
        config = []
        config.append(
            {
                "ros_topic_name": "/clock",
                "gz_topic_name": "/clock",
                "ros_type_name": "rosgraph_msgs/msg/Clock",
                "gz_type_name": "gz.msgs.Clock",
                "direction": "GZ_TO_ROS",
            }
        )
        for platform in platforms:
            ns = platform.namespace
            if platform.platform_type in {"Lidar", "Beamagine"}:
                config.append(
                    {
                        "ros_topic_name": f"/{ns}/scan/points",
                        "gz_topic_name": f"/{ns}/scan/points",
                        "ros_type_name": "sensor_msgs/msg/PointCloud2",
                        "gz_type_name": "gz.msgs.PointCloudPacked",
                        "direction": "GZ_TO_ROS",
                    }
                )
            if platform.platform_type in {"Camera", "Beamagine"}:
                # Define camera topics and remappings for ros_gz_image bridge:
                image_topics = [f"/{ns}/image", f"/{ns}/depth_image"]
                remaps = [f"/{ns}/color/image", f"/{ns}/depth/image"]
                sub_topics = ["compressed", "compressedDepth", "theora", "zstd"]
                self.image_topics.extend(image_topics)
                for topic, remap in zip(image_topics, remaps, strict=False):
                    self.image_remaps.append((topic, remap))
                    for sub_topic in sub_topics:
                        self.image_remaps.append(
                            (f"{topic}/{sub_topic}", f"{remap}/{sub_topic}")
                        )

                # Bridge camera_info and points using normal gz_ros_bridge:
                config.append(
                    {
                        "ros_topic_name": f"/{ns}/color/camera_info",
                        "gz_topic_name": f"/{ns}/camera_info",
                        "ros_type_name": "sensor_msgs/msg/CameraInfo",
                        "gz_type_name": "gz.msgs.CameraInfo",
                        "direction": "GZ_TO_ROS",
                    }
                )
                config.append(
                    {
                        "ros_topic_name": f"/{ns}/depth/camera_info",
                        "gz_topic_name": f"/{ns}/camera_info",
                        "ros_type_name": "sensor_msgs/msg/CameraInfo",
                        "gz_type_name": "gz.msgs.CameraInfo",
                        "direction": "GZ_TO_ROS",
                    }
                )
                match platform.name:
                    case "zed":
                        points_frame_id = f"/{ns}/{ns}_left_camera_frame"
                    case "realsense":
                        points_frame_id = f"/{ns}/camera_color_frame"
                    case _:
                        points_frame_id = None
                if points_frame_id:
                    config.append(
                        {
                            "ros_topic_name": f"/{ns}/points",
                            "gz_topic_name": f"/{ns}/points",
                            "ros_type_name": "sensor_msgs/msg/PointCloud2",
                            "gz_type_name": "gz.msgs.PointCloudPacked",
                            "frame_id": points_frame_id,
                            "direction": "GZ_TO_ROS",
                        }
                    )

            if platform.platform_type == "GPS":
                config.append(
                    {
                        "ros_topic_name": f"/{ns}/gps/fix_raw",
                        "gz_topic_name": f"/{ns}/gps/fix_raw",
                        "ros_type_name": "sensor_msgs/msg/NavSatFix",
                        "gz_type_name": "gz.msgs.NavSat",
                        "direction": "GZ_TO_ROS",
                    }
                )
            if platform.platform_type in {"ThermalCamera", "Beamagine"}:
                config.append(
                    {
                        "ros_topic_name": f"/{ns}/thermal/image",
                        "gz_topic_name": f"/{ns}/thermal/image",
                        "ros_type_name": "sensor_msgs/msg/Image",
                        "gz_type_name": "gz.msgs.Image",
                        "direction": "GZ_TO_ROS",
                    }
                )
            if platform.platform_type == "IMU":
                config.append(
                    {
                        "ros_topic_name": f"/{ns}/imu/data",
                        "gz_topic_name": f"/{ns}/imu/data",
                        "ros_type_name": "sensor_msgs/msg/Imu",
                        "gz_type_name": "gz.msgs.IMU",
                        "direction": "GZ_TO_ROS",
                    }
                )
        with open(self.config_file, "w", encoding="utf-8") as outfile:
            yaml.dump(config, outfile, sort_keys=False)
