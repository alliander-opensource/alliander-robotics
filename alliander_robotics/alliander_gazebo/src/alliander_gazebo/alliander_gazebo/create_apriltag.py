# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

import numpy as np
import PIL
import requests
import trimesh
import trimesh.visual
import xmltodict
from alliander_utilities.config_objects import Apriltag
from alliander_utilities.ros_utils import get_file_path
from PIL import Image
from rclpy.node import Node

FAMILIY = "36h11"


def create_apriltag(tag: Apriltag, node: Node) -> None:
    """Create a 3D model of an AprilTag using trimesh and export it as a GLB file.

    Args:
        tag (Apriltag): The AprilTag configuration object.
        node (Node): The ROS2 node used for logging.
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

    sdf_path = get_file_path("alliander_gazebo", ["models", "apriltag"], "model.sdf")
    with open(sdf_path, encoding="utf-8") as fd:
        sdf_string = fd.read()

    sdf_dict = xmltodict.parse(sdf_string)
    sdf_dict["sdf"]["model"]["link"]["collision"]["geometry"]["mesh"]["uri"] = (
        f"/tmp/apriltag_{tag.id}.glb"
    )
    sdf_dict["sdf"]["model"]["link"]["visual"]["geometry"]["mesh"]["uri"] = (
        f"/tmp/apriltag_{tag.id}.glb"
    )

    with open(f"/tmp/apriltag_{tag.id}.sdf", "w", encoding="utf-8") as fd:
        fd.write(xmltodict.unparse(sdf_dict))
