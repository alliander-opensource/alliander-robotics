# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

import pytest
from alliander_utilities.config_objects import Arm
from rclpy.node import Node
from sensor_msgs.msg import JointState

from ..utils import (
    assert_for_message,
    call_move_to_configuration_service,
    call_trigger_action,
    check_joint_positions,
    follow_joint_trajectory_goal,
    wait_until_reached_joint,
)

arm = Arm("franka", gripper=True, moveit=True)
PLATFORMS = [arm]


class _TestArm:
    """Base class for arm tests.

    Attributes:
         platforms (dict): A dictionary of the platforms to launch.
    """

    platforms: dict

    def test_joint_states_published(self) -> None:
        """Test that joint states are published."""
        assert_for_message(
            JointState, f"/{self.platforms['arm'].namespace}/joint_states", timeout=100
        )

    @pytest.mark.parametrize(
        "action, expected_value",
        [("open", 0.04), ("close", 0.00)],
    )
    def test_gripper_action(
        self,
        action: str,
        expected_value: float,
        test_node: Node,
        finger_joint_fault_tolerance: float,
        timeout: int,
    ) -> None:
        """Test gripper open/close action and verify joint state.

        Args:
            action (str): The action to call.
            expected_value (float): The expected joint value after the action.
            test_node (Node): The test node to use for the test.
            finger_joint_fault_tolerance (float): The tolerance for the finger joint position.
            timeout (int): The timeout in seconds before stopping the test.
        """
        assert (
            call_trigger_action(
                test_node,
                f"{self.platforms['arm'].namespace}/gripper/{action}",
                timeout=timeout,
            )
            is True
        )
        reached_goal, joint_value = wait_until_reached_joint(
            namespace=self.platforms["arm"].namespace,
            joint="fr3_finger_joint1",
            expected_value=expected_value,
            tolerance=finger_joint_fault_tolerance,
            timeout_sec=timeout,
        )
        assert reached_goal is True, (
            f"The joint did not reach the joint. Currently {joint_value}, expected {expected_value}"
        )

    def test_follow_joint_trajectory_goal(
        self, test_node: Node, joint_movement_tolerance: float, timeout: int
    ) -> None:
        """Test following a joint trajectory goal.

        Args:
            test_node (Node): The test node to use for the test.
            joint_movement_tolerance (float): The tolerance for joint movement.
            timeout (int): The timeout in seconds to wait for the joint trajectory goal to be followed.
        """
        expected_positions = [0.15, -0.39, 0.1, -2.06, 0.0, 1.68, 1.01]
        follow_joint_trajectory_goal(
            test_node,
            positions=expected_positions,
            controller=f"{self.platforms['arm'].namespace}/fr3_arm_controller",
            timeout=timeout,
        )
        joint_names = [f"fr3_joint{i + 1}" for i in range(7)]
        check_joint_positions(
            self.platforms["arm"].namespace,
            joint_names,
            expected_positions,
            joint_movement_tolerance,
            timeout,
        )

    def test_move_to_drop_configuration(
        self, test_node: Node, joint_movement_tolerance: float, timeout: int
    ) -> None:
        """Test that MoveIt can move to a configuration.

        Args:
            test_node (Node): The test node to use for the test.
            joint_movement_tolerance (float): The tolerance for joint movement.
            timeout (int): The timeout in seconds before stopping the test.
        """
        assert call_move_to_configuration_service(
            test_node, self.platforms["arm"].namespace, "drop", timeout=timeout
        ), "Failed to call move_to_configuration service."
        joint_names = [f"fr3_joint{i + 1}" for i in range(7)]
        expected_positions = [-1.57079632679, -0.65, 0, -2.4, 0, 1.75, 0.78539816339]
        check_joint_positions(
            self.platforms["arm"].namespace,
            joint_names,
            expected_positions,
            joint_movement_tolerance,
            timeout,
        )


for arm in ["franka"]:
    arm_platform = Arm(arm, (0, 0, 0.5), gripper=True, moveit=True)
    test_class = type(
        f"Test{arm.capitalize()}",
        (_TestArm,),
        {"platforms": {"arm": arm_platform}},
    )
    globals()[test_class.__name__] = test_class
