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


class Lidar(Platform):
    """Extension on Platform with lidar specific functionalities.

    Attributes:
        SUPPORTED_PLATFORMS: The supported platforms.
    """

    SUPPORTED_PLATFORMS = Literal["velodyne", "ouster"]

    def __init__(  # noqa: PLR0913
        self,
        platform: SUPPORTED_PLATFORMS,
        position: list,
        orientation: list | None = None,
        namespace: str | None = None,
        parent: Vehicle | None = None,
        parent_link: str = "",
    ):
        """Initialize the Lidar platform.

        Args:
            platform (SUPPORTED_PLATFORMS): The platform type.
            position (list): The position of the lidar.
            orientation (list | None): The initial orientation of the lidar.
            namespace (str | None): The namespace of the lidar.
            parent (Vehicle | None): The parent platform.
            parent_link (str): The link of the parent to which the platform is attached. If empty, the base_link of the parent is used.
        """
        super().__init__(
            platform, position, orientation, namespace, parent, parent_link
        )

        if parent:
            parent.lidar = self

        Rviz.add_point_cloud(self.namespace)
        Rviz.add_laser_scan(self.namespace)
        Vizanti.add_laser_scan(self.namespace)
        EnvironmentConfiguration.bridge_topics.append(
            f"/{self.namespace}/scan/points@sensor_msgs/msg/PointCloud2@gz.msgs.PointCloudPacked"
        )

    @property
    def base_link(self) -> str:  # noqa: PLR0911
        """Return the base link for the LiDAR sensor.

        Returns:
            str: The base link for the LiDAR sensor.
        """
        return "base_link"

    @property
    def xacro_path(self) -> str:  # noqa: PLR0911
        """Return the xacro file path for the LiDAR sensor.

        Returns:
            str: The xacro file path for the LiDAR sensor.

        Raises:
            ValueError: If the platform is unknown.
        """
        match self.platform_type:
            case "velodyne":
                return get_file_path(
                    "rcdt_sensors", ["urdf"], "rcdt_velodyne.urdf.xacro"
                )
            case "ouster":
                return get_file_path(
                    "rcdt_sensors", ["urdf"], "rcdt_os1_128.urdf.xacro"
                )
            case _:
                raise ValueError("Cannot provide xacro path: unknown LiDAR platform.")

    def create_launch_description(self) -> list[RegisteredLaunchDescription]:
        """Create the launch description with specific elements for a lidar.

        Returns:
            list[RegisteredLaunchDescription]: The launch description for the platform.
        """
        launch_descriptions = []
        if self.platform_type == "velodyne":
            launch_descriptions.append(self.create_velodyne_launch())
        if self.platform_type == "ouster":
            launch_descriptions.append(self.create_ouster_launch())
        return launch_descriptions

    def create_velodyne_launch(self) -> RegisteredLaunchDescription:
        """Create the Velodyne launch description.

        Returns:
            RegisteredLaunchDescription: The launch description for Velodyne.
        """
        if self.parent:
            target_frame = f"{self.parent.namespace}/{self.parent.base_link}"
        else:
            target_frame = f"{self.namespace}/base_link"

        return RegisteredLaunchDescription(
            get_file_path("rcdt_sensors", ["launch"], "velodyne.launch.py"),
            launch_arguments={
                "simulation": str(EnvironmentConfiguration.simulation),
                "namespace": self.namespace,
                "target_frame": target_frame,
            },
        )

    def create_ouster_launch(self) -> RegisteredLaunchDescription:
        """Create the Ouster launch description.

        Returns:
            RegisteredLaunchDescription: The launch description for Ouster.
        """
        if self.parent:
            target_frame = f"{self.parent.namespace}/{self.parent.base_link}"
        else:
            target_frame = f"{self.namespace}/base_link"

        return RegisteredLaunchDescription(
            get_file_path("rcdt_sensors", ["launch"], "ouster.launch.py"),
            launch_arguments={
                "simulation": str(EnvironmentConfiguration.simulation),
                "namespace": self.namespace,
                "target_frame": target_frame,
            },
        )
