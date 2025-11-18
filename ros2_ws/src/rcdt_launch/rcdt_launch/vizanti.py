# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

import json

from rcdt_utilities.ros_utils import get_file_path


class Vizanti:
    """A class to dynammically manage the Vizanti configuration.

    Attributes:
        config (dict): The default Vizanti configuration.
    """

    config: dict

    with open(
        get_file_path("rcdt_panther", ["config"], "vizanti_config.json"),
        encoding="utf-8",
    ) as json_file:
        config = json.load(json_file)

    @staticmethod
    def create_config_file() -> None:
        """Create the Vizanti configuration file."""
        with open("/tmp/vizanti.json", "w", encoding="utf-8") as outfile:
            json.dump(Vizanti.config, outfile)

    @staticmethod
    def add_platform_model(namespace: str) -> None:
        """Add a robot model to the Vizanti configuration.

        Args:
            namespace (str): The namespace of the robot.
        """
        Vizanti.config["navbar"].append(
            {"type": "robotmodel", "id": "robotmodel", "container_id": "icon_container"}
        )
        Vizanti.config["robotmodel"] = {
            "frame": f"{namespace}/base_footprint",
            "sprite": "jaguar",
            "opacity": "1.0",
            "length": "0.5",
            "offset_x": "0.0",
            "offset_y": "0.0",
            "offset_yaw": "0.0",
        }

    @staticmethod
    def add_button(name: str, topic: str, msg_type: str | None = None) -> None:
        """Add a button to the Vizanti configuration.

        Args:
            name (str): The name of the button.
            topic (str): The topic connected to.
            msg_type (str | None): The message type of the topic.
        """
        Vizanti.config["navbar"].append(
            {"type": "button", "id": name, "container_id": "icon_container"}
        )
        Vizanti.config[name] = {
            "topic": topic,
            "text": name,
            "typedict": {topic: msg_type} if msg_type else {},
        }

    @staticmethod
    def add_initial_pose() -> None:
        """Add an initial pose setter to the Vizanti configuration."""
        Vizanti.config["navbar"].append(
            {
                "type": "initialpose",
                "id": "initialpose",
                "container_id": "icon_container",
            }
        )
        Vizanti.config["initialpose"] = {"topic": "/initialpose"}

    @staticmethod
    def add_goal_pose() -> None:
        """Add a goal pose setter to the Vizanti configuration."""
        Vizanti.config["navbar"].append(
            {"type": "simplegoal", "id": "simplegoal", "container_id": "icon_container"}
        )
        Vizanti.config["simplegoal"] = {"topic": "/goal_pose"}

    @staticmethod
    def add_waypoints(namespace: str) -> None:
        """Add a waypoint setter to the Vizanti configuration.

        Args:
            namespace (str): The namespace of the robot.
        """
        Vizanti.config["navbar"].append(
            {"type": "waypoints", "id": "waypoints", "container_id": "icon_container"}
        )
        Vizanti.config["waypoints"] = {
            "topic": "/waypoints",
            "topic_type": "nav_msgs/msg/Path",
            "fixed_frame": "map",
            "base_link_frame": f"{namespace}/base_link",
            "points": [],
        }

    @staticmethod
    def add_laser_scan(namespace: str) -> None:
        """Add a laser scan to the Vizanti configuration.

        Args:
            namespace (str): The namespace of the robot.
        """
        Vizanti.config["navbar"].append(
            {
                "type": "scan",
                "id": f"scan_{namespace}",
                "container_id": "icon_container",
            }
        )
        Vizanti.config[f"scan_{namespace}"] = {
            "topic": f"/{namespace}/scan",
            "opacity": "1",
            "thickness": "0.02",
            "color": "#ff0000",
            "throttle": "2000",
        }

    @staticmethod
    def add_map(name: str, topic: str) -> None:
        """Add a map to the Vizanti configuration.

        Args:
            name (str): The name of the map.
            topic (str): The topic of the map.
        """
        Vizanti.config["navbar"].append(
            {"type": "map", "id": f"map_{name}", "container_id": "icon_container"}
        )
        Vizanti.config[f"map_{name}"] = {
            "topic": topic,
            "opacity": "0.7",
            "colour_scheme": 1,
            "throttle": "100",
            "use_timestamp": False,
        }

    @staticmethod
    def add_path(topic: str) -> None:
        """Add a path to the Vizanti configuration.

        Args:
            topic (str): The topic of the path.
        """
        Vizanti.config["navbar"].append(
            {"type": "path", "id": "path", "container_id": "icon_container"}
        )
        Vizanti.config["path"] = {"topic": topic, "color": "#54db67", "throttle": "100"}
