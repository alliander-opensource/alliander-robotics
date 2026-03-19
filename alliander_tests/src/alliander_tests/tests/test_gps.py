# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

from alliander_utilities.config_objects import GPS
from sensor_msgs.msg import NavSatFix

from ..utils import assert_for_message


class _TestGPS:
    """Base class for GPS tests.

    Attributes:
         platforms (dict): A dictionary of the platforms to launch.
    """

    platforms: dict

    def test_gps_fix_published(self, timeout: int) -> None:
        """Test that the gps fix messages are published.

        Args:
            timeout (int): The timeout in seconds to wait for the messages to be published.
        """
        assert_for_message(
            NavSatFix, f"/{self.platforms['gps'].namespace}/gps/fix", timeout=timeout
        )


for gps in ["gps"]:
    gps_platform = GPS(gps, (0, 0, 0.5))
    test_class = type(
        f"Test{gps.capitalize()}",
        (_TestGPS,),
        {"platforms": {"gps": gps_platform}},
    )
    globals()[test_class.__name__] = test_class
