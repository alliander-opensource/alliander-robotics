# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

import numpy as np
import requests
import trimesh
import trimesh.visual
from PIL import Image


def create_apriltag() -> None:
    """Create a 3D model of an AprilTag using trimesh and export it as a GLB file."""
    tag_size = 0.22
    thickness = 0.001

    url = "https://raw.githubusercontent.com/AprilRobotics/apriltag-imgs/master/tag36h11/tag36_11_00000.png"
    img = np.array(Image.open(requests.get(url, stream=True).raw))
    rows, cols, _ = img.shape
    size = tag_size / (rows - 2)

    meshes = []
    transform = np.eye(4)
    transform[0, -1] = -(rows * size) / 2 + size / 2
    transform[1, -1] = -(cols * size) / 2 + size / 2
    for row in range(rows):
        for col in range(cols):
            mesh: trimesh.Trimesh = trimesh.creation.box(
                [size, size, thickness], transform
            )
            color = img[row, col]
            material = trimesh.visual.material.PBRMaterial(baseColorFactor=color)
            mesh.visual = trimesh.visual.TextureVisuals(material=material)
            meshes.append(mesh)
            transform[1, -1] += size
        transform[1, -1] = -(cols * size) / 2 + size / 2
        transform[0, -1] += size

    combined_mesh = trimesh.util.concatenate(meshes)
    combined_mesh.export("/tmp/apriltag.glb", file_type="glb")
