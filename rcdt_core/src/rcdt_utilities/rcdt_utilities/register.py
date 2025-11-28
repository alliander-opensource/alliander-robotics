# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import Any

from launch import LaunchContext, LaunchDescription
from launch.actions import (
    ExecuteProcess,
    IncludeLaunchDescription,
    OpaqueFunction,
    RegisterEventHandler,
)
from launch.event_handlers import OnProcessExit, OnProcessIO, OnProcessStart
from launch.events.process import ProcessIO
from launch_ros.actions import Node
from rclpy import logging
from termcolor import colored

LOGGER = logging.get_logger("Register")
CONF_NAME = "registered_group"


class RegisteredLaunchDescription(IncludeLaunchDescription):
    """Extends on the default IncludeLaunchDescription, to automatically register an unique group_id.

    Atributes:
        launch_description_source (str): The path to the launch file to include.
        launch_arguments (dict): The launch arguments to pass to the included launch file.
    """

    def __init__(
        self, launch_description_source: str, launch_arguments: dict | None = None
    ):
        """Initializes the RegisteredLaunchDescription with a unique group_id.

        Args:
            launch_description_source (str): The path to the launch file to include.
            launch_arguments (dict | None): The launch arguments to pass to the included launch file. Defaults to None.
        """
        if launch_arguments is None:
            launch_arguments = {}
        self.group_id = Register.get_unique_group_id()
        launch_arguments[CONF_NAME] = self.group_id
        super().__init__(
            launch_description_source,
            launch_arguments=launch_arguments.items(),
        )


class Register:
    """A class to register the individual processes from launch files, to ensure a desired launch order.

    This class is used to register actions that should be started in a specific order, based on the order of registration.
    It uses a static list to keep track of the registered actions and their order.
    The actions can be of type Node or ExecuteProcess, and can be registered to start on specific events, such as on start, on exit, or on log messages.
    The class also provides methods to reset the register, get the next action to start, and group registered launch descriptions together.

    Attributes:
        group_id (int): A unique identifier for the group of registered actions.
        register (list["Register" | str]): A list of registered actions, which can be of type Node or ExecuteProcess, or a string representing a group.
        actions (int): The total number of actions registered.
        started (int): The number of actions that have been started.
        all_started (bool): A flag indicating whether all registered actions have been started.
    """

    group_id: int = 0
    register: list["Register" | str] = []
    actions: int = 0
    started: int = 0
    all_started: bool = False

    @staticmethod
    def get_unique_group_id() -> str:
        """Get a unique group id based on a ascending counter.

        Returns:
            str: A unique group id in the format "group_{id}".
        """
        Register.group_id += 1
        return f"group_{Register.group_id}"

    @staticmethod
    def reset() -> None:
        """Reset the register. Useful for pytest since it can launch ros multiple times in the same session."""
        Register.group_id = 0
        Register.register = []
        Register.actions = 0
        Register.started = 0

    @staticmethod
    def next(*_: Any) -> LaunchDescription:
        """Returns the next action to start based on the order of registration.

        Args:
            *_ (Any): Ignored. Additional arguments from `OnProcessStart` or `OnProcessExit`.

        Returns:
            LaunchDescription: A launch description containing the next action to start, or an empty launch description if all actions have been started.
        """
        item = None
        Register.started += 1
        while not isinstance(item, Register):
            if len(Register.register) == 1:
                log_progress()
                Register.all_started = True
                Register.reset()
                return LaunchDescription([])
            item = Register.register.pop(1)
        log_progress(item.action)
        return LaunchDescription([item.action])

    @staticmethod
    def group(
        launch_description: RegisteredLaunchDescription, context: LaunchContext
    ) -> RegisteredLaunchDescription:
        """Adds a the group id of the included launch_description to the register.

        This enables the items of the included launch description to register in the right order later.

        Args:
            launch_description (RegisteredLaunchDescription): The launch description to register.
            context (LaunchContext): The launch context to get the group id from.

        Returns:
            RegisteredLaunchDescription: The launch description with the group id registered.
        """
        name = launch_description.group_id
        group = context.launch_configurations.get(CONF_NAME)

        if group:
            index = Register.register.index(group)
            Register.register.insert(index, name)
        else:
            Register.register.append(name)
        return launch_description

    @staticmethod
    def connect_context(
        groups: list[RegisteredLaunchDescription],
    ) -> LaunchDescription:
        """Returns a LaunchDescription of an OpaqueFunction, so that LaunchContext is available.

        This LaunchContext is required for the Register methods to correctly link the different groups of included launch files.

        Args:
            groups (list[RegisteredLaunchDescription]): A list of RegisteredLaunchDescription objects to be included in the launch description.

        Returns:
            LaunchDescription: A LaunchDescription containing an OpaqueFunction that sets up the launch items.
        """

        def launch_setup(
            context: LaunchContext,
            registered_launch_descriptions: list[RegisteredLaunchDescription],
        ) -> list:
            launch_items = []
            for description in registered_launch_descriptions:
                if not isinstance(description, RegisteredLaunchDescription):
                    raise TypeError
                launch_items.append(Register.group(description, context))
            return launch_items

        opaque_function = OpaqueFunction(function=launch_setup, args=[groups])
        return LaunchDescription([opaque_function])

    def __init__(self):
        """Initializes the Register class with default values."""
        self.action: Node | ExecuteProcess | None = None

        self.is_started = False
        self.log: str
        self.buffer: str = "\n"

    @classmethod
    def on_start(
        cls, action: Node | ExecuteProcess, context: LaunchContext
    ) -> LaunchDescription:
        """Registers the given action to be ready directly on start.

        This method is used to register an action that should be started immediately when the launch file is executed.

        Args:
            action (Node | ExecuteProcess): The action to register, which can be a Node or ExecuteProcess.
            context (LaunchContext): The launch context to get the group id from.

        Returns:
            LaunchDescription: A launch description containing the action and an event handler to trigger the next action.
        """
        register = cls()
        event_handler = RegisterEventHandler(
            OnProcessStart(target_action=action, on_start=Register.next)
        )
        return register.insert_action(action, event_handler, context)

    @classmethod
    def on_exit(
        cls, action: Node | ExecuteProcess, context: LaunchContext
    ) -> LaunchDescription:
        """Registers the given action to be ready on exit.

        This method is used to register an action that should be started when the specified action exits.

        Args:
            action (Node | ExecuteProcess): The action to register, which can be a Node or ExecuteProcess.
            context (LaunchContext): The launch context to get the group id from.

        Returns:
            LaunchDescription: A launch description containing the action and an event handler to trigger the next action on exit.
        """
        register = cls()
        event_handler = RegisterEventHandler(
            OnProcessExit(target_action=action, on_exit=Register.next)
        )
        return register.insert_action(action, event_handler, context)

    @classmethod
    def on_log(
        cls, action: Node | ExecuteProcess, log: str, context: LaunchContext
    ) -> LaunchDescription:
        """Registers the given action to be ready when logging the given log message.

         This method is used to register an action that should be started when a specific log message is captured.

        Args:
            action (Node | ExecuteProcess): The action to register, which can be a Node or ExecuteProcess.
            log (str): The log message to capture before starting the action.
            context (LaunchContext): The launch context to get the group id from.

        Returns:
            LaunchDescription: A launch description containing the action and an event handler to trigger the next action when the log message is captured.
        """
        register = cls()
        register.log = log
        event_handler = RegisterEventHandler(
            OnProcessIO(target_action=action, on_stderr=register.process_io)
        )

        return register.insert_action(action, event_handler, context)

    def process_io(self, event: ProcessIO) -> None:
        """Returns the next register to start if the defined log is captured.

        This method is called when a log message is captured from the action's stderr.
        If the log message contains the defined log, it sets the started flag to True and returns the next action to start.

        Args:
            event (ProcessIO): The event containing the log message.
        """
        if self.is_started:
            return

        buffer = event.text.decode()
        if self.buffer.endswith("\n"):
            self.buffer = buffer
        else:
            self.buffer += buffer

        if self.log in self.buffer:
            self.is_started = True
            return Register.next()

    def insert_action(
        self,
        action: Node | ExecuteProcess,
        event_handler: RegisterEventHandler,
        context: LaunchContext,
    ) -> LaunchDescription:
        """Inserts the action in the register and returns a launch description.

        If a group is defined, the index is defined based on the index of the group.
        Otherwise, the index is simply the length of the register, so that the item is appended at the end.
        A launch description is returned with the event_handler.
        If the item is the first action to start, the launch_description also contains the action to trigger the chain reaction.

        Args:
            action (Node | ExecuteProcess): The action to register, which can be a Node or ExecuteProcess.
            event_handler (RegisterEventHandler): The event handler to trigger the next action.
            context (LaunchContext): The launch context to get the group id from.

        Returns:
            LaunchDescription: A launch description containing the action and the event handler.
        """
        self.action = action
        group = context.launch_configurations.get(CONF_NAME)
        index = Register.register.index(group) if group else len(Register.register)
        Register.register.insert(index, self)
        Register.actions += 1

        if index == 0:
            log_progress(action)
            Register.all_started = False
            return LaunchDescription([action, event_handler])
        else:
            return LaunchDescription([event_handler])


def log_progress(action: Node | ExecuteProcess | None = None) -> None:
    """Logs the progress of the registered actions.

    This function logs the current state of the registered actions, including how many actions have been started and the total number of actions.
    If no action is provided, it logs that all actions have been started.
    It also formats the log message with colors for better visibility.

    Args:
        action (Node | ExecuteProcess | None): The action that has been started, or None if all actions have been started.
    """
    if Register.started == 0:
        msg = "[START] "
    else:
        msg = f"[{Register.started}/{Register.actions}] "

    if isinstance(action, Node):
        msg += "(node) " + action.node_package + " " + action.node_executable
    elif isinstance(action, ExecuteProcess):
        msg += "(process) "
        for part in action.cmd:
            msg += part[0].text + " "
    elif not action:
        msg += "All actions are started!"

    LOGGER.info(colored(msg, "blue"))
