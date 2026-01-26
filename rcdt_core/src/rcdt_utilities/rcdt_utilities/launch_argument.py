# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

from launch import LaunchContext
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration


class LaunchArgument:
    """A class to handle launch arguments in ROS 2 launch files.

    This class allows you to declare a launch argument with a default value and optional choices.
    It also provides a method to retrieve the value of the argument in a launch context.
    """

    def __init__(
        self,
        name: str,
        default_value: str | bool | int | float,
        choices: list | None = None,
        min_value: float | None = None,
        max_value: float | None = None,
    ) -> None:
        """Initializes a LaunchArgument instance.

        Args:
            name (str): The name of the launch argument.
            default_value (str | bool | int | float): The default value of the launch argument.
            choices (list | None): A list of valid choices for the launch argument. Defaults to None.
            min_value (float | None): The minimum value for the launch argument if it is a number. Defaults to None.
            max_value (float | None): The maximum value for the launch argument if it is a number. Defaults to None.
        """
        self.configuration = LaunchConfiguration(name)
        self.min_value = min_value
        self.max_value = max_value
        if choices is not None:
            choices = [str(choice) for choice in choices]
            self.declaration = DeclareLaunchArgument(
                name=name, default_value=str(default_value), choices=choices
            )
        else:
            self.declaration = DeclareLaunchArgument(
                name=name, default_value=str(default_value)
            )

    def string_value(self, context: LaunchContext) -> str:
        """Retrieve the string value of the launch argument in a given context.

        Args:
            context (LaunchContext): The launch context in which to evaluate the argument.

        Returns:
            str: The string value of the launch argument.
        """
        return self.configuration.perform(context)

    def bool_value(self, context: LaunchContext) -> bool:
        """Retrieve the boolean value of the launch argument in a given context.

        Args:
            context (LaunchContext): The launch context in which to evaluate the argument.

        Raises:
            TypeError: If the string value cannot be interpreted as a boolean.

        Returns:
            bool: The boolean value of the launch argument.
        """
        string_value = self.string_value(context)
        if string_value in {"True", "true"}:
            return True
        elif string_value in {"False", "false"}:
            return False
        else:
            raise TypeError

    def int_value(self, context: LaunchContext) -> int:
        """Retrieve the integer value of the launch argument in a given context.

        Args:
            context (LaunchContext): The launch context in which to evaluate the argument.

        Returns:
            int: The integer value of the launch argument.
        """
        string_value = self.string_value(context)
        return int(string_value)

    def float_value(self, context: LaunchContext) -> float:
        """Retrieve the float value of the launch argument in a given context.

        Args:
            context (LaunchContext): The launch context in which to evaluate the argument.

        Raises:
            RuntimeError: If the float value is outside the specified min or max range.

        Returns:
            float: The float value of the launch argument.
        """
        string_value = self.string_value(context)
        float_value = float(string_value)
        if self.min_value is not None and float_value < self.min_value:
            raise RuntimeError(
                f"'Value must be ≥ {self.min_value}, but got {float_value}"
            )
        if self.max_value is not None and float_value > self.max_value:
            raise RuntimeError(
                f"'Value must be ≤ {self.max_value}, but got {float_value}"
            )
        return float_value
