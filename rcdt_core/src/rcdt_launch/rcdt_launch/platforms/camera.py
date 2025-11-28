# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from rcdt_launch.environment_configuration import EnvironmentConfiguration
from rcdt_launch.platforms.platform import Platform
from rcdt_launch.rviz import Rviz
from rcdt_utilities.register import RegisteredLaunchDescription
from rcdt_utilities.ros_utils import get_file_path

if TYPE_CHECKING:
    from rcdt_launch.platforms.arm import Arm
    from rcdt_launch.platforms.vehicle import Vehicle


class Camera(Platform):
    """Extension on Platform with camera specific functionalities."""

    def __init__(  # noqa: PLR0913
        self,
        platform: Literal["realsense", "zed"],
        position: list,
        orientation: list | None = None,
        namespace: str | None = None,
        parent: Arm | Vehicle | None = None,
        parent_link: str = "",
    ):
        """Initialize the Camera platform.

        Args:
            platform (Literal["realsense", "zed"]): The platform type.
            position (list): The position of the camera.
            orientation (list | None): The initial orientation of the camera.
            namespace (str | None): The namespace of the camera.
            parent (Arm | Vehicle | None): The parent platform.
            parent_link (str): The link of the parent to which the platform is attached. If empty, the base_link of the parent is used.
        """
        super().__init__(
            platform, position, orientation, namespace, parent, parent_link
        )

        if parent:
            parent.camera = self

        Rviz.add_image(f"/{self.namespace}/color/image_raw")
        Rviz.add_image(f"/{self.namespace}/depth/image_rect_raw")
        Rviz.add_depth_cloud(
            f"/{self.namespace}/color/image_raw",
            f"/{self.namespace}/depth/image_rect_raw",
        )

        EnvironmentConfiguration.bridge_topics.extend(
            [
                f"/{self.namespace}/color/camera_info@sensor_msgs/msg/CameraInfo@gz.msgs.CameraInfo",
                f"/{self.namespace}/color/image_raw@sensor_msgs/msg/Image@gz.msgs.Image",
                f"/{self.namespace}/depth/camera_info@sensor_msgs/msg/CameraInfo@gz.msgs.CameraInfo",
                f"/{self.namespace}/depth/image_rect_raw_float@sensor_msgs/msg/Image@gz.msgs.Image",
            ]
        )

    @property
    def base_link(self) -> str:  # noqa: PLR0911
        """Return the base link for the camera.

        Returns:
            str: The base link for the camera.
        """
        return "base_link"

    @property
    def xacro_path(self) -> str:  # noqa: PLR0911
        """Return the xacro file path for the camera.

        Returns:
            str: The xacro file path for the camera.

        Raises:
            ValueError: If the Camera platform is unknown.
        """
        match self.platform_type:
            case "realsense":
                return get_file_path(
                    "rcdt_sensors", ["urdf"], "rcdt_realsense_d435.urdf.xacro"
                )
            case "zed":
                return get_file_path("rcdt_sensors", ["urdf"], "rcdt_zed2i.urdf.xacro")
            case _:
                raise ValueError("Cannot provide xacro path: unknown Camera platform.")

    def create_launch_description(self) -> list[RegisteredLaunchDescription]:
        """Create the launch description with specific elements for a camera.

        Returns:
            list[RegisteredLaunchDescription]: The launch description for the platform.
        """
        launch_descriptions = []
        if self.platform_type == "realsense":
            launch_descriptions.append(self.create_realsense_launch())
        if self.platform_type == "zed":
            launch_descriptions.append(self.create_zed_launch())
        return launch_descriptions

    def create_zed_launch(self) -> RegisteredLaunchDescription:
        """Create the Zed launch description.

        Returns:
            RegisteredLaunchDescription: The launch description for the Zed.
        """
        return RegisteredLaunchDescription(
            get_file_path("rcdt_sensors", ["launch"], "zed.launch.py"),
            launch_arguments={
                "simulation": str(EnvironmentConfiguration.simulation),
                "namespace": self.namespace,
            },
        )

    def create_realsense_launch(self) -> RegisteredLaunchDescription:
        """Create the Realsense launch description.

        Returns:
            RegisteredLaunchDescription: The launch description for the Realsense.
        """
        return RegisteredLaunchDescription(
            get_file_path("rcdt_sensors", ["launch"], "realsense.launch.py"),
            launch_arguments={
                "simulation": str(EnvironmentConfiguration.simulation),
                "namespace": self.namespace,
            },
        )
