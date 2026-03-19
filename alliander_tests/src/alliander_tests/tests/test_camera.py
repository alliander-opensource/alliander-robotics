# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

from alliander_utilities.config_objects import Camera
from sensor_msgs.msg import CameraInfo, Image

from ..utils import assert_for_message


class _TestCamera:
    """Base class for camera tests.

    Attributes:
         platforms (dict): A dictionary of the platforms to launch.
    """

    platforms: dict

    def test_color_image_published(self, timeout: int) -> None:
        """Test that color images are published.

        Args:
            timeout (int): The timeout in seconds.
        """
        assert_for_message(
            Image,
            f"/{self.platforms['camera'].namespace}/color/image_raw",
            timeout=timeout,
        )

    def test_color_camera_info_published(self, timeout: int) -> None:
        """Test that color camera info is published.

        Args:
            timeout (int): The timeout in seconds.
        """
        assert_for_message(
            CameraInfo,
            f"/{self.platforms['camera'].namespace}/color/camera_info",
            timeout=timeout,
        )

    def test_depth_image_published(self, timeout: int) -> None:
        """Test that depth images are published.

        Args:
            timeout (int): The timeout in seconds.
        """
        assert_for_message(
            Image,
            f"/{self.platforms['camera'].namespace}/depth/image_rect_raw",
            timeout=timeout,
        )

    def test_depth_camera_info_published(self, timeout: int) -> None:
        """Test that color camera info is published.

        Args:
            timeout (int): The timeout in seconds.
        """
        assert_for_message(
            CameraInfo,
            f"/{self.platforms['camera'].namespace}/depth/camera_info",
            timeout=timeout,
        )


for camera in ["realsense", "zed"]:
    camera_platform = Camera(camera, (0, 0, 0.5))
    test_class = type(
        f"Test{camera.capitalize()}",
        (_TestCamera,),
        {"platforms": {"camera": camera_platform}},
    )
    globals()[test_class.__name__] = test_class
