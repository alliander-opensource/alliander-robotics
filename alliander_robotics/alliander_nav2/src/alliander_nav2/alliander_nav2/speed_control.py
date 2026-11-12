# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

from dataclasses import dataclass

from rcl_interfaces.msg import Parameter, ParameterType, ParameterValue
from rcl_interfaces.srv import GetParameters, SetParameters
from rclpy.node import Node


@dataclass
class Speed:
    """Class representing the maximum speed of the robot.

    Attributes:
        linear (float): The maximum linear speed of the robot in meters per second.
        angular (float): The maximum angular speed of the robot in radians per second.
    """

    linear: float
    angular: float


class SpeedControl:
    """Class for controlling the speed of the robot."""

    def __init__(self, node: Node):
        """Initialize.

        Args:
            node (Node): The ROS 2 node used for creating clients and logging.
        """
        self.node = node
        self.logger = node.get_logger()
        self.timeout = 3
        self.controller_server_get_parameters = node.create_client(
            GetParameters, "controller_server/get_parameters"
        )
        self.controller_server_set_parameters = node.create_client(
            SetParameters, "controller_server/set_parameters"
        )

    def set_max_speed(self, speed: Speed) -> bool:
        """Set the speed of the robot by updating the controller server parameters.

        Args:
            speed (Speed): The desired speed for the robot.

        Returns:
            bool: True if the speed was successfully set, False otherwise.
        """
        # Define parameters:
        param_lin_speed = Parameter()
        param_lin_speed.name = "FollowPath.vx_max"
        param_lin_speed.value = ParameterValue(
            type=ParameterType.PARAMETER_DOUBLE, double_value=speed.linear
        )

        param_ang_speed = Parameter()
        param_ang_speed.name = "FollowPath.wz_max"
        param_ang_speed.value = ParameterValue(
            type=ParameterType.PARAMETER_DOUBLE, double_value=speed.angular
        )

        param_ang_speed_heading = Parameter()
        param_ang_speed_heading.name = "FollowPath.rotate_to_heading_angular_vel"
        param_ang_speed_heading.value = ParameterValue(
            type=ParameterType.PARAMETER_DOUBLE, double_value=speed.angular
        )

        parameters = [param_lin_speed, param_ang_speed, param_ang_speed_heading]

        # Get current speed and remove parameters that are already set:
        request = GetParameters.Request()
        request.names = [param.name for param in parameters]
        if not self.controller_server_get_parameters.wait_for_service(self.timeout):
            self.logger.error("Controller server get parameters service not available.")
            return False
        response = self.controller_server_get_parameters.call(request, self.timeout)
        if not isinstance(response, GetParameters.Response):
            self.logger.error("Failed to get current speed limit due to no response.")
            return False
        parameters_to_update = []
        for param, value in zip(parameters, response.values, strict=True):
            if param.value.double_value == value.double_value:
                self.logger.debug(f"{param.name} is {param.value.double_value}")
            else:
                parameters_to_update.append(param)

        # If no parameters need updating, return:
        if not parameters_to_update:
            return True

        # Change speed for parameters that need updating:
        request = SetParameters.Request()
        request.parameters = parameters_to_update
        if not self.controller_server_set_parameters.wait_for_service(self.timeout):
            self.logger.error("Controller server set parameters service not available.")
            return False
        response = self.controller_server_set_parameters.call(request, self.timeout)
        if not isinstance(response, SetParameters.Response):
            self.logger.error("Failed to set speed due to no response.")
            return False

        for param, result in zip(parameters_to_update, response.results, strict=True):
            if result.successful:
                self.logger.info(f"{param.name} set to {param.value.double_value}")
            else:
                self.logger.error(f"Failed to set speed: {result.reason}")
        return all(result.successful for result in response.results)
