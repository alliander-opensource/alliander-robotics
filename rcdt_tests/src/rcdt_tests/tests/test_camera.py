# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

import random

from rcdt_utilities.config_objects import Camera
from sensor_msgs.msg import CameraInfo, Image

from ..utils import assert_for_message

camera = Camera(random.choice(["realsense", "zed"]), (0, 0, 0.5))
PLATFORMS = {camera.name: camera}


def test_color_image_published(timeout: int) -> None:
    """Test that color images are published.

    Args:
        timeout (int): The timeout in seconds.
    """
    assert_for_message(Image, f"/{camera.namespace}/color/image_raw", timeout=timeout)


def test_color_camera_info_published(timeout: int) -> None:
    """Test that color camera info is published.

    Args:
        timeout (int): The timeout in seconds.
    """
    assert_for_message(
        CameraInfo, f"/{camera.namespace}/color/camera_info", timeout=timeout
    )


def test_depth_image_published(timeout: int) -> None:
    """Test that depth images are published.

    Args:
        timeout (int): The timeout in seconds.
    """
    assert_for_message(
        Image, f"/{camera.namespace}/depth/image_rect_raw", timeout=timeout
    )


def test_depth_camera_info_published(timeout: int) -> None:
    """Test that color camera info is published.

    Args:
        timeout (int): The timeout in seconds.
    """
    assert_for_message(
        CameraInfo, f"/{camera.namespace}/depth/camera_info", timeout=timeout
    )
