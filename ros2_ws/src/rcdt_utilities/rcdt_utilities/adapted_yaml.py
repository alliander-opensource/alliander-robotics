# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

import os

import yaml
from pydantic.v1.utils import deep_update

from rcdt_utilities.ros_utils import get_yaml


class AdaptedYaml:
    """Class to adapt a YAML file with parameter substitutions, based on Nav2's RewrittenYaml."""

    def __init__(self, source_file: str, param_rewrites: dict, root_key: str) -> None:
        """Rewrite the parameters under the `ros__parameters` key in source_file with param_rewrites and place in root_key namespace.

        Args:
            source_file (str): Path to the original YAML file.
            param_rewrites (dict): Dictionary of the parameters to rewrite.
            root_key (str): The root key (namespace) to wrap the parameters.
        """
        base_name = os.path.basename(source_file)
        namespace, ros_params = self.get_ros_params(source_file)
        ros_params = deep_update(ros_params, param_rewrites)
        namespace.insert(0, root_key)
        self.file = self.write_params(ros_params, namespace, base_name)

    @staticmethod
    def get_ros_params(source_file: str) -> tuple[list[str], dict]:
        """Extract the 'ros__parameters' dictionary and its namespace from the source file.

        Args:
            source_file (str): Path to the YAML file.

        Raises:
            KeyError: If no or multiple 'ros__parameters' keys are found.

        Returns:
            tuple[list[str], dict]: A tuple containing the namespace as a list of strings and the
            'ros__parameters' dictionary.
        """
        params = get_yaml(source_file)
        sub_dicts: list[tuple[list[str], dict]] = [([], params)]
        ros_params: list[tuple[list[str], dict]] = []
        while len(sub_dicts) > 0:
            layer, current_dict = sub_dicts.pop()
            for key, value in current_dict.items():
                if key == "ros__parameters":
                    ros_params.append((layer + [key], value))
                elif isinstance(value, dict):
                    sub_dicts.append((layer + [key], value))

        if len(ros_params) == 0:
            raise KeyError(f"No 'ros__parameters' key found in {source_file}")
        if len(ros_params) > 1:
            raise KeyError(f"Multiple 'ros__parameters' keys found in {source_file}")

        return ros_params[0]

    @staticmethod
    def write_params(ros_params: dict, namespaces: list[str], base_name: str) -> str:
        """Write ros parameters to a namespaced YAML file.

        Args:
            ros_params (dict): The ros parameters to write.
            namespaces (list[str]): The namespaces for the parameters.
            base_name (str): The base name for the output file.

        Returns:
            str: The path to the written YAML file.
        """
        namespaces.reverse()
        params = ros_params
        for namespace in namespaces:
            params = {namespace: params}
        file = "/tmp/" + base_name
        with open(file, "w", encoding="utf-8") as outfile:
            yaml.dump(params, outfile, default_flow_style=False)
        return file
