#!/usr/bin/env python3
# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

import re
import subprocess

import numpy as np
import rclpy
from rclpy.node import Node
from scipy.spatial.transform import RigidTransform, Rotation


class SpawnPlatform(Node):
    """Node to spawn platforms in the Gazebo simulation."""

    def __init__(self):
        """Initialize the node."""
        super().__init__("spawn_platforms")
        self.declare_parameter("platforms", "")
        self.declare_parameter("positions", "")
        self.declare_parameter("orientations", "")
        self.declare_parameter("parents", "")
        self.declare_parameter("parent_links", "")
        platforms = (
            self.get_parameter("platforms").get_parameter_value().string_value.split()
        )
        positions = (
            self.get_parameter("positions").get_parameter_value().string_value.split()
        )
        orientations = (
            self.get_parameter("orientations")
            .get_parameter_value()
            .string_value.split()
        )
        parents = (
            self.get_parameter("parents").get_parameter_value().string_value.split()
        )
        parent_links = (
            self.get_parameter("parent_links")
            .get_parameter_value()
            .string_value.split()
        )

        self.get_logger().info("Spawning platforms...")
        self.spawn_platforms(platforms, positions, orientations, parents, parent_links)
        self.get_logger().info("All platforms spawned!")

    def spawn_platforms(
        self,
        platforms: list[str],
        positions: list[str],
        orientations: list[str],
        parents: list[str],
        parent_links: list[str],
    ) -> None:
        """Spawn platforms in the Gazebo simulation at specified positions.

        Args:
            platforms (list[str]): List of the platforms.
            positions (list[str]): List of positions in the format "x,y,z".
            orientations (list[str]): List of orientations in the format "roll,pitch,yaw".
            parents (list[str]): List of parent names or "none" when the platform has no parent.
            parent_links (list[str]): List of parent link names or "none" when the platform has no parent.

        """
        for n in range(len(platforms)):
            platform = platforms[n]
            position = np.array(list(map(float, positions[n].split(","))))
            orientation = np.array(list(map(float, orientations[n].split(","))))
            parent = parents[n]
            parent_link = parent_links[n]

            if parent != "none":
                # First define the transform from world to model:
                model_pose = get_pose(parent)
                model_tf = RigidTransform.from_components(
                    model_pose["position"],
                    Rotation.from_euler("xyz", model_pose["orientation"]),
                )

                # Next define the transform from model to link:
                link_pose = get_pose(parent, parent_link)
                link_tf = RigidTransform.from_components(
                    link_pose["position"],
                    Rotation.from_euler("xyz", link_pose["orientation"]),
                )

                # Finally, combine the transforms and apply the given position and orientation:
                tf = model_tf * link_tf
                position = tf.apply(position)
                rotation = tf.rotation * Rotation.from_euler("xyz", orientation)
                orientation = rotation.as_euler("xyz")

            self.spawn_platform(platform, position, orientation)

    def spawn_platform(
        self, namespace: str, position: np.ndarray, orientation: np.ndarray
    ) -> None:
        """Spawn a platform in the Gazebo simulation with a specified position and orientation.

        Args:
            namespace (str): The namespace of the platform.
            position (np.ndarray): The position [x, y, z] of the platform.
            orientation (np.ndarray): The orientation [roll, pitch, yaw] of the platform.
        """
        self.get_logger().info(f"Spawn: {namespace} {position} {orientation}")
        x, y, z = position
        roll, pitch, yaw = orientation
        subprocess.run(
            [
                "ros2",
                "run",
                "ros_gz_sim",
                "create",
                "-topic",
                f"/{namespace}/robot_description",
                "-name",
                namespace,
                "-x",
                str(x),
                "-y",
                str(y),
                "-z",
                str(z),
                "-R",
                str(roll),
                "-P",
                str(pitch),
                "-Y",
                str(yaw),
            ],
            check=True,
        )


def get_pose(model: str, link: str | None = None) -> dict:
    """Get the pose of a model or a specific link of a model in the Gazebo simulation.

    Args:
        model (str): The name of the model.
        link (str | None): The name of the link.

    Returns:
        dict: A dictionary with the position and orientation of the link.

    Raises:
        RuntimeError: If the link info could not be retrieved or parsed.
    """
    command = ["gz", "model", "-m", model]
    if link:
        command.extend(["-l", link])
    message = subprocess.check_output(command, stderr=subprocess.DEVNULL).decode(
        "utf-8"
    )

    lines = message.splitlines()
    line_of_interest = None
    for n, line in enumerate(lines):
        if line == "  - Pose [ XYZ (m) ] [ RPY (rad) ]:":
            if line_of_interest is not None:
                raise RuntimeError("Found multiple lines containing pose information.")
            line_of_interest = n
    if line_of_interest is None:
        raise RuntimeError(f"Could not find pose information for {model} - {link}.")
    position = lines[line_of_interest + 1]
    orientation = lines[line_of_interest + 2]
    return {
        "position": process_string(position),
        "orientation": process_string(orientation),
    }


def process_string(info_string: str) -> np.ndarray:
    """Process the info string to extract the position or orientation values.

    Args:
        info_string (str): The info string.

    Returns:
        np.ndarray: An array of float values extracted from the info string.

    Raises:
        RuntimeError: If the info string is not in the expected format.
    """
    values_string = re.search(r"\[(.*?)\]", info_string)

    if not values_string:
        raise RuntimeError("Could not parse message.")

    group = values_string.group(1)
    return np.array(list(map(float, group.split())))


def main(args: list | None = None) -> None:
    """Main function to initialize the ROS 2 node and set the thresholds.

    Args:
        args (list | None): Command line arguments, defaults to None.
    """
    rclpy.init(args=args)
    spawn_platform = SpawnPlatform()
    spawn_platform.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
