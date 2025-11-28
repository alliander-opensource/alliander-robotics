# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from rcdt_launch.environment_configuration import EnvironmentConfiguration
from rcdt_launch.platforms.platform import Platform
from rcdt_launch.rviz import Rviz
from rcdt_launch.vizanti import Vizanti
from rcdt_utilities.register import RegisteredLaunchDescription
from rcdt_utilities.ros_utils import get_file_path

if TYPE_CHECKING:
    from rcdt_launch.platforms.vehicle import Vehicle


class GPS(Platform):
    """Extension on Platform with GPS specific functionalities."""

    def __init__(  # noqa: PLR0913
        self,
        platform: Literal["nmea"],
        position: list,
        orientation: list | None = None,
        namespace: str | None = None,
        parent: Vehicle | None = None,
        ip_address: str = "",
    ):
        """Initialize the GPS platform.

        Args:
            platform (Literal["nmea"]): The platform type.
            position (list): The position of the platform.
            orientation (list | None): The orientation of the platform.
            namespace (str | None): The namespace of the platform.
            parent (Vehicle | None): The parent platform.
            ip_address (str): The IP address of the platform.
        """
        super().__init__(platform, position, orientation, namespace, parent)
        self.platform_type = platform
        self.namespace = self.namespace
        self.ip_address = ip_address

        if parent:
            parent.gps = self

        EnvironmentConfiguration.bridge_topics.append(
            f"/{self.namespace}/gps/fix@sensor_msgs/msg/NavSatFix@gz.msgs.NavSat"
        )

        Rviz.add_satellite(f"/{self.namespace}/gps/filtered")
        Vizanti.add_satellite(f"/{self.namespace}/gps/filtered")

    @property
    def base_link(self) -> str:  # noqa: PLR0911
        """Return the base link for the GPS sensor.

        Returns:
            str: The base link for the GPS sensor.
        """
        return "base_link"

    @property
    def xacro_path(self) -> str:  # noqa: PLR0911
        """Return the xacro file path for the GPS sensor.

        Returns:
            str: The xacro file path for the GPS sensor.

        Raises:
            ValueError: If the platform is unknown.
        """
        match self.platform_type:
            case "nmea":
                return get_file_path(
                    "rcdt_sensors", ["urdf"], "rcdt_nmea_navsat.urdf.xacro"
                )
            case _:
                raise ValueError("Cannot provide xacro path: unknown GPS platform.")

    def create_launch_description(self) -> list[RegisteredLaunchDescription]:
        """Create the launch description with specific elements for a camera.

        Returns:
            list[RegisteredLaunchDescription]: The launch description for the platform.
        """
        launch_descriptions = []
        if self.platform_type == "nmea":
            launch_descriptions.append(self.create_nmea_launch())
        return launch_descriptions

    def create_nmea_launch(self) -> RegisteredLaunchDescription:
        """Create the NMEA launch description.

        Returns:
            RegisteredLaunchDescription: The launch description for the Realsense.
        """
        return RegisteredLaunchDescription(
            get_file_path("rcdt_sensors", ["launch"], "nmea_navsat.launch.py"),
            launch_arguments={
                "simulation": str(EnvironmentConfiguration.simulation),
                "namespace_vehicle": self.parent.namespace if self.parent else "",
                "namespace_gps": self.namespace,
                "ip_address": self.ip_address,
            },
        )
