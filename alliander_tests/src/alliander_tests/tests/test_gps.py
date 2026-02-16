# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

from alliander_utilities.config_objects import GPS
from sensor_msgs.msg import NavSatFix

from ..utils import assert_for_message

gps = GPS("gps", (0, 0, 0.5))
PLATFORMS = [gps]


def test_gps_fix_published(timeout: int) -> None:
    """Test that the gps fix messages are published.

    Args:
        timeout (int): The timeout in seconds to wait for the messages to be published.
    """
    assert_for_message(NavSatFix, f"/{gps.namespace}/gps/fix", timeout=timeout)
