# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

import os
from os import environ

from ament_index_python.packages import get_package_share_directory
from catkin_pkg.package import (
    PACKAGE_MANIFEST_FILENAME,
    Export,
    InvalidPackage,
    Package,
    parse_package,
)
from ros2pkg.api import get_package_names


class GazeboRosPaths:
    """Based on: https://github.com/gazebosim/ros_gz/blob/ros2/ros_gz_sim/launch/gz_sim.launch.py.in.

    By using our own launch file we are able to launch Gazebo as process with shell=False.
    This avoids ghost processes of Gazebo continuing and might be implemented in the original launch file in the future:
    https://github.com/gazebosim/ros_gz/issues/563
    """

    @staticmethod
    def get_paths() -> tuple[str, str]:
        """Get the paths for Gazebo models and plugins.

        Returns:
            tuple[str, str]: A tuple containing the model paths and plugin paths.
        """
        gazebo_model_path = []
        gazebo_plugin_path = []
        gazebo_media_path = []

        for package_name in get_package_names():
            package_share_path = get_package_share_directory(package_name)
            package_file_path = os.path.join(
                package_share_path, PACKAGE_MANIFEST_FILENAME
            )
            if os.path.isfile(package_file_path):
                try:
                    package: Package = parse_package(package_file_path)
                except InvalidPackage:
                    continue
                for export in package.exports:
                    export: Export
                    if export.tagname == "gazebo_ros":
                        if "gazebo_model_path" in export.attributes:
                            xml_path = export.attributes["gazebo_model_path"]
                            xml_path: str = xml_path.replace(
                                "${prefix}", package_share_path
                            )
                            gazebo_model_path.append(xml_path)
                        if "plugin_path" in export.attributes:
                            xml_path = export.attributes["plugin_path"]
                            xml_path = xml_path.replace("${prefix}", package_share_path)
                            gazebo_plugin_path.append(xml_path)
                        if "gazebo_media_path" in export.attributes:
                            xml_path = export.attributes["gazebo_media_path"]
                            xml_path = xml_path.replace("${prefix}", package_share_path)
                            gazebo_media_path.append(xml_path)

        gazebo_model_path = os.pathsep.join(gazebo_model_path + gazebo_media_path)
        gazebo_plugin_path = os.pathsep.join(gazebo_plugin_path)

        return gazebo_model_path, gazebo_plugin_path

    @staticmethod
    def get_env() -> dict[str, str]:
        """Get the environment variables for Gazebo.

        Returns:
            dict[str, str]: A dictionary containing the environment variables.
        """
        model_paths, plugin_paths = GazeboRosPaths.get_paths()
        env = {
            "GZ_SIM_SYSTEM_PLUGIN_PATH": os.pathsep.join(
                [
                    environ.get("GZ_SIM_SYSTEM_PLUGIN_PATH", default=""),
                    environ.get("LD_LIBRARY_PATH", default=""),
                    plugin_paths,
                ]
            ),
            "GZ_SIM_RESOURCE_PATH": os.pathsep.join(
                [
                    environ.get("GZ_SIM_RESOURCE_PATH", default=""),
                    model_paths,
                ]
            ),
        }
        return env
