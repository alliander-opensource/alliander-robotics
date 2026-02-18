# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0
import json

from alliander_utilities.ros_utils import get_file_path


class Foxglove:
    """A class to dynammically manage the Foxglove layout.

    Attributes:
        layout (dict): The default Foxglove layout.
    """

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
                if reference["first"] == {}:
                    reference["first"] = {
                        "first": {},
                        "second": {},
                        "direction": direction,
                    }
                    references.append(reference["first"])
                else:
                    reference["second"] = {
                        "first": {},
                        "second": {},
                        "direction": direction,
                    }
                    references.append(reference["second"])
                    references.pop(0)
                places += 1
            elif reference["first"] == {}:
                reference["first"] = panels.pop(0)
            else:
                reference["second"] = panels.pop(0)
                references.pop(0)

        Foxglove.layout["layout"] = layout
        with open("/foxglove_layout.json", "w", encoding="utf-8") as outfile:
            json.dump(Foxglove.layout, outfile)

    @staticmethod
    def add_platform_model(namespace: str) -> None:
        """Add a robot model to the Foxglove layout.

        Args:
            namespace (str): The namespace of the robot.
        """
        Foxglove.layout["configById"]["3D"]["layers"][f"urdf-{namespace}"] = {
            "layerId": "foxglove.Urdf",
            "sourceType": "topic",
            "topic": f"/{namespace}/robot_description",
            "framePrefix": f"{namespace}/",
        }

    @staticmethod
    def add_camera(namespace: str) -> None:
        """Add a camera feed to the Foxglove layout.

        Args:
            namespace (str): The namespace of the robot.
        """
        Foxglove.layout["configById"][f"Image_{namespace}"] = {
            "imageMode": {
                "imageTopic": f"/{namespace}/zed/color/image_raw",
                "calibrationTopic": f"/{namespace}/zed/color/camera_info",
            }
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
