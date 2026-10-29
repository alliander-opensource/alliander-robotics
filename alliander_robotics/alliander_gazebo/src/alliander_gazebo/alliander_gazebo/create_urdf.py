# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

import numpy as np
import PIL
import requests
import trimesh
import trimesh.visual
from alliander_utilities.config_objects import Apriltag, ChargingStation
from alliander_utilities.ros_utils import get_file_path, get_robot_description
from PIL import Image
from rclpy.node import Node

FAMILIY = "36h11"


def create_apriltag(tag: Apriltag, node: Node) -> str:
    """Create a 3D model of an AprilTag using trimesh and export it as a GLB file and a URDF file.

    Args:
        tag (Apriltag): The AprilTag configuration object.
        node (Node): The ROS2 node used for logging.

    Returns:
        str: The path to the generated URDF file.
    """
    filename = FAMILIY.replace("h", "_") + f"_{tag.id:05d}" + ".png"
    url = f"https://raw.githubusercontent.com/AprilRobotics/apriltag-imgs/master/tag{FAMILIY}/tag{filename}"
    try:
        img = np.array(Image.open(requests.get(url, stream=True).raw))
    except PIL.UnidentifiedImageError as _:
        node.get_logger().error(
            "Failed to download AprilTag image. Falling back to red plane."
        )
        img = np.array([[[255, 0, 0]]])
    rows, cols, _ = img.shape
    size = tag.size / (rows - 2)

    meshes = []
    transform = np.eye(4)
    transform[0, -1] = -(rows * size) / 2 + size / 2
    transform[1, -1] = -(cols * size) / 2 + size / 2
    for row in range(rows):
        for col in range(cols):
            mesh: trimesh.Trimesh = trimesh.creation.box(
                [size, size, tag.thickness], transform
            )
            color = img[row, col]
            material = trimesh.visual.material.PBRMaterial(baseColorFactor=color)
            mesh.visual = trimesh.visual.TextureVisuals(material=material)
            meshes.append(mesh)
            transform[1, -1] += size
        transform[1, -1] = -(cols * size) / 2 + size / 2
        transform[0, -1] += size

    combined_mesh = trimesh.util.concatenate(meshes)
    combined_mesh.export(f"/tmp/apriltag_{tag.id}.glb", file_type="glb")

    xacro_file = get_file_path("alliander_description", ["urdf"], "apriltag.urdf.xacro")
    xacro_args = {"index": str(tag.id), "parent": "" if tag.parent.link else "world"}
    urdf = get_robot_description(xacro_file, xacro_args)["robot_description"]
    urdf_path = f"/tmp/apriltag_{tag.id}.urdf"
    with open(urdf_path, "w", encoding="utf-8") as f:
        f.write(urdf)
    return urdf_path


def create_charging_station(station: ChargingStation) -> str:
    """Create a URDF file for the charging station.

    Args:
        station (ChargingStation): The charging station configuration object.

    Returns:
        str: The path to the generated URDF file.
    """
    xacro_file = get_file_path(
        "alliander_husarion_description",
        ["urdf"],
        "wibotic_station.urdf.xacro",
    )
    xacro_args = {
        "childs": str(
            [
                [child.connects_to, child.namespace, child.link]
                for child in station.childs
            ]
        )
    }
    urdf = get_robot_description(xacro_file, xacro_args)["robot_description"]
    urdf_path = "/tmp/charging_station.urdf"
    with open(urdf_path, "w", encoding="utf-8") as f:
        f.write(urdf)
    return urdf_path
