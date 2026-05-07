# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

from alliander_utilities.config_objects import Lidar
from sensor_msgs.msg import PointCloud2

from ..utils import assert_for_message


class _TestLidar:
    """Base class for Lidar tests.

    Attributes:
         platforms (dict): A dictionary of the platforms to launch.
    """

    platforms: dict

    def test_points_published(self, timeout: int) -> None:
        """Test that the pointcloud is published.

        Args:
            timeout (int): The timeout in seconds to wait for the points to be published.
        """
        assert_for_message(
            PointCloud2,
            f"/{self.platforms['lidar'].namespace}/scan/points",
            timeout=timeout,
        )


for lidar in ["velodyne", "ouster"]:
    lidar_platform = Lidar(lidar, (0, 0, 0.5))
    test_class = type(
        f"Test{lidar.capitalize()}",
        (_TestLidar,),
        {"platforms": {"lidar": lidar_platform}},
    )
    globals()[test_class.__name__] = test_class
