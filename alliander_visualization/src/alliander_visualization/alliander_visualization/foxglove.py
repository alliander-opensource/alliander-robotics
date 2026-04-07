# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0
import json

from alliander_utilities.ros_utils import get_file_path


class Foxglove:
    """A class to dynammically manage the Foxglove layout.

    Attributes:
        topics (list): The topics to bridge.
        services (list): The services to bridge.
        layout (dict): The Foxglove layout.
    """

    topics: list = ["/clock", "/tf", "/tf_static"]
    services: list = [""]
    layout: dict

    with open(
        get_file_path("alliander_visualization", ["config"], "foxglove_layout.json"),
        encoding="utf-8",
    ) as json_file:
        layout = json.load(json_file)

    @staticmethod
    def create_layout_file() -> None:
        """Create the Foxglove layout file."""
        panels = list(Foxglove.layout["configById"].keys())

        layout = {"first": {}, "second": {}, "direction": "row"}
        references = [layout]

        if len(panels) == 1:
            layout = panels.pop()

        places = 2
        while len(panels) > 0:
            reference = references[0]
            direction = "row" if reference["direction"] == "column" else "column"
            if places < len(panels):
                if reference["second"] == {}:
                    reference["second"] = {
                        "first": {},
                        "second": {},
                        "direction": direction,
                    }
                    references.append(reference["second"])
                else:
                    reference["first"] = {
                        "first": {},
                        "second": {},
                        "direction": direction,
                    }
                    references.append(reference["first"])
                    references.pop(0)
                places += 1
            elif reference["second"] == {}:
                reference["second"] = panels.pop()
            else:
                reference["first"] = panels.pop()
                references.pop(0)

        Foxglove.layout["layout"] = layout
        with open("/foxglove.json", "w", encoding="utf-8") as outfile:
            json.dump(Foxglove.layout, outfile)

    @staticmethod
    def add_platform_model(namespace: str) -> None:
        """Add a robot model to the Foxglove layout.

        Args:
            namespace (str): The namespace of the robot.
        """
        Foxglove.topics.append([f"/{namespace}/robot_description"])
        Foxglove.layout["configById"]["3D"]["layers"][f"urdf-{namespace}"] = {
            "layerId": "foxglove.Urdf",
            "sourceType": "topic",
            "topic": f"/{namespace}/robot_description",
            "framePrefix": f"{namespace}/",
        }

    @staticmethod
    def add_street_map(namespace: str) -> None:
        """Add a street map to the Foxglove 3D panel.

        Args:
            namespace (str): The namespace of the platform.
        """
        Foxglove.topics.append(f"/{namespace}/gps/fix")
        Foxglove.topics.append(f"/{namespace}/gps/filtered")
        Foxglove.layout["configById"]["3D"]["layers"]["map"] = {
            "layerId": "foxglove.TiledMap",
            "visible": True,
            "serverConfig": "map",
            "label": "Map",
        }

    @staticmethod
    def add_image(namespace: str) -> None:
        """Add a camera feed to the Foxglove layout.

        Args:
            namespace (str): The namespace of the platform.
        """
        Foxglove.topics.append(f"/{namespace}/color/image_raw")
        Foxglove.topics.append(f"/{namespace}/color/camera_info")
        Foxglove.layout["configById"][f"Image!{namespace}"] = {
            "imageMode": {
                "imageTopic": f"/{namespace}/color/image_raw",
                "calibrationTopic": f"/{namespace}/color/camera_info",
            }
        }

    @staticmethod
    def add_pointcloud(namespace: str) -> None:
        """Add a pointcloud to the Foxglove 3D panel.

        Args:
            namespace (str): The namespace of the platform.
        """
        Foxglove.topics.append(f"/{namespace}/scan/points")
        Foxglove.layout["configById"]["3D"]["topics"][f"/{namespace}/scan/points"] = {
            "visible": True,
            "colorMode": "colormap",
            "colorMap": "rainbow",
            "colorField": "intensity",
        }

    @staticmethod
    def add_map(topic: str) -> None:
        """Add a map to the Foxglove 3D panel.

        Args:
            topic (str): The topic of the costmap.
        """
        Foxglove.topics.append(topic)
        Foxglove.layout["configById"]["3D"]["topics"][topic] = {
            "visible": True,
            "colorMode": "costmap",
        }

    @staticmethod
    def add_path(topic: str) -> None:
        """Add a path to the Foxglove 3D panel.

        Args:
            topic (str): The topic of the path.
        """
        Foxglove.topics.append(topic)
        Foxglove.layout["configById"]["3D"]["topics"][topic] = {
            "visible": True,
            "lineWidth": 0.03,
            "gradient": ["#00ff00ff", "#00ff00ff"],
        }

    @staticmethod
    def add_polygon(topic: str) -> None:
        """Add a polygon to the Foxglove 3D panel.

        Args:
            topic (str): The topic of the polygon.
        """
        Foxglove.topics.append(topic)

    @staticmethod
    def add_trigger_service(name: str, service: str) -> None:
        """Add a service call panel to the Foxglove layout.

        Args:
            name (str): The name of the button.
            service (str): The service to call when the button is pressed.
        """
        Foxglove.services.append(service)
        Foxglove.layout["configById"][f"CallService!{name}"] = {
            "serviceName": service,
            "foxglovePanelTitle": service,
            "editingMode": False,
            "buttonText": name,
        }

    @staticmethod
    def add_joystick(namespace: str) -> None:
        """Add a virtual joystick to the Foxglove layout.

        Args:
            namespace (str): The namespace of the robot.
        """
        Foxglove.layout["configById"]["virtual-joystick.Virtual Joystick"]["topic"] = (
            f"/{namespace}/cmd_vel"
        )
