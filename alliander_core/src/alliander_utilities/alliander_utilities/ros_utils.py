# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

import contextlib
import os

import rclpy
import xacro
import yaml
from ament_index_python.packages import get_package_share_directory
from rclpy.executors import Executor
from rclpy.node import Node


def get_file_path(package: str, folders: list[str], file: str) -> str:
    """Construct a file path within a ROS 2 package.

    Args:
        package (str): The name of the ROS 2 package.
        folders (list[str]): A list of folder names leading to the file.
        file (str): The name of the file.

    Returns:
        str: The full path to the specified file within the package.
    """
    package_path = get_package_share_directory(package)
    return os.path.join(package_path, *folders, file)


def get_yaml(file_path: str) -> dict:
    """Load a YAML file and return its contents as a dictionary.

    Args:
        file_path (str): The path to the YAML file.

    Returns:
        dict: The contents of the YAML file as a dictionary.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return yaml.safe_load(file)
    except EnvironmentError:
        return {}


def get_robot_description(
    xacro_path: str, xacro_arguments: dict | None = None, semantic: bool = False
) -> dict:
    """Process a Xacro file to generate the robot description.

    Args:
        xacro_path (str): The path to the Xacro file.
        xacro_arguments (dict | None): A dictionary of arguments to pass to the Xacro processor.
        semantic (bool): Whether to return the semantic robot description.

    Returns:
        dict: A dictionary containing the robot description in XML format.
    """
    if xacro_arguments is None:
        xacro_arguments = {}
    robot_description_config = xacro.process_file(xacro_path, mappings=xacro_arguments)
    name = "robot_description_semantic" if semantic else "robot_description"
    return {name: robot_description_config.toxml()}


def spin_node(node: Node) -> None:
    """Spin a ROS 2 node to process callbacks and keep it alive.

    Args:
        node (Node): The ROS 2 node to spin.
    """
    with contextlib.suppress(KeyboardInterrupt):
        rclpy.spin(node)


def spin_executor(executor: Executor) -> None:
    """Spin a ROS 2 executor to process callbacks from multiple nodes.

    Args:
        executor (Executor): The ROS 2 executor to spin.
    """
    with contextlib.suppress(KeyboardInterrupt):
        executor.spin()
