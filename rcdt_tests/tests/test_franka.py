from rcdt_utilities.config_objects import Arm
from rcdt_utilities.test_utils import assert_for_message
from sensor_msgs.msg import JointState

arm = Arm("franka")
PLATFORMS = {arm.name: arm}


def test_joint_states_published() -> None:
    """Test that joint states are published."""
    assert_for_message(JointState, f"/{arm.namespace}/joint_states", timeout=100)
