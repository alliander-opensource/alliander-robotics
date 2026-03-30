# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

import numpy as np
import pytest
import xmltodict
from alliander_utilities.config_objects import Arm
from control_msgs.msg import JointTrajectoryControllerState
from rclpy.node import Node
from sensor_msgs.msg import JointState

from ..utils import (
    assert_for_message,
    call_move_to_configuration_service,
    call_trigger_action,
    check_joint_positions,
    follow_joint_trajectory_goal,
    get_message,
    get_parameter,
    wait_until_reached_joint,
)


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
        if self.platforms["arm"].name == "ur":
            pytest.skip("Gripper is not yet implemented for UR arm.")
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
        # Get joint names and current position and define a goal position:
        controller_state = get_message(
            JointTrajectoryControllerState,
            f"/{self.platforms['arm'].namespace}/joint_trajectory_controller/controller_state",
            timeout=timeout,
        )
        current_positions = list(controller_state.reference.positions)
        goal_positions = [position + np.deg2rad(10) for position in current_positions]

        # Call the follow_joint_trajectory action and check if the joints reached the expected positions:
        follow_joint_trajectory_goal(
            test_node,
            controller_state.joint_names,
            goal_positions,
            controller=f"{self.platforms['arm'].namespace}/joint_trajectory_controller",
            timeout=timeout,
        )
        check_joint_positions(
            self.platforms["arm"].namespace,
            controller_state.joint_names,
            goal_positions,
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
        # Get the robot_description_semantic and convert to a dictionary:
        robot_description_semantic_str = get_parameter(
            test_node,
            f"/{self.platforms['arm'].namespace}/move_group",
            "robot_description_semantic",
            timeout=timeout,
        ).string_value
        robot_description_semantic = xmltodict.parse(robot_description_semantic_str)

        # Extract the configurations from the robot_description_semantic:
        configurations = {}
        group_states = robot_description_semantic["robot"]["group_state"]
        for group_state in group_states:
            configurations[group_state["@name"]] = {"names": [], "positions": []}
            for joint in group_state["joint"]:
                configurations[group_state["@name"]]["names"].append(joint["@name"])
                configurations[group_state["@name"]]["positions"].append(
                    joint["@value"]
                )

        # Call the move_to_configuration service and check if the joints reached the expected positions:
        configuration = "drop"
        names = configurations[configuration]["names"]
        positions = [float(pos) for pos in configurations[configuration]["positions"]]
        assert call_move_to_configuration_service(
            test_node, self.platforms["arm"].namespace, configuration, timeout=timeout
        ), "Failed to call move_to_configuration service."
        check_joint_positions(
            self.platforms["arm"].namespace,
            names,
            positions,
            joint_movement_tolerance,
            timeout,
        )


for arm in ["franka", "ur"]:
    arm_platform = Arm(arm, (0, 0, 0.5), gripper=True, moveit=True)
    test_class = type(
        f"Test{arm.capitalize()}",
        (_TestArm,),
        {"platforms": {"arm": arm_platform}},
    )
    globals()[test_class.__name__] = test_class
