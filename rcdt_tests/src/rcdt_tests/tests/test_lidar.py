# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

import random

from rcdt_utilities.config_objects import Lidar
from sensor_msgs.msg import PointCloud2

from ..utils import assert_for_message

lidar = Lidar(random.choice(["velodyne", "ouster"]), (0, 0, 0.5))
PLATFORMS = {lidar.name: lidar}


def test_points_published(timeout: int) -> None:
    """Test that the pointcloud is published.

    Args:
        timeout (int): The timeout in seconds to wait for the points to be published.
    """
    assert_for_message(PointCloud2, f"/{lidar.namespace}/scan/points", timeout=timeout)
