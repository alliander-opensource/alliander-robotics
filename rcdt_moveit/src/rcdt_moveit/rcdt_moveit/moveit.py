# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

import xmltodict
from moveit_configs_utils import MoveItConfigs, MoveItConfigsBuilder
from rcdt_utilities.ros_utils import get_file_path, get_robot_description, get_yaml


class Moveit:
    """A class to dynamically manage the MoveIt configuration.

    Attributes:
        configurations (dict[str, MoveItConfigs]): A dictionary containing the MoveIt configurations for each namespace.
        servo_configurations (dict[str, dict]): A dictionary containing the MoveIt Servo configurations for each namespace.
    """

    configurations: dict[str, MoveItConfigs] = {}
    servo_configurations: dict[str, dict] = {}

    @staticmethod
    def add(namespace: str, robot_description: dict, platform: str) -> None:
        """Add a MoveIt configuration.

        This method creates a moveit configuration using the MoveItConfigsBuilder.
        The robot description and semantic description are adapted to include the namespace as prefix.
        This adaption is require, since MoveIt otherwise uses the /robot_description topic directly, where the prefixes are not published.
        The prefixes are only published to the /tf topic by the robot_state_publisher.

        Args:
            namespace (str): The namespace of the robot.
            robot_description (dict): The robot description dictionary.
            platform (str): The platform of the robot.
        """
        match platform:
            case "franka":
                package = "rcdt_franka_moveit_config"
        srdf_path = get_file_path(package, ["config"], "fr3.srdf")
        moveit_config_builder = MoveItConfigsBuilder(platform, package_name=package)

        # load servos configuration:
        servo_params_path = get_file_path(package, ["config"], "servo_params.yaml")
        servo_config = get_yaml(servo_params_path)
        for param in ["joint_topic", "command_out_topic"]:
            value = servo_config[param]
            servo_config[param] = "/" + namespace + value

        # load yaml's to moveit_configs:
        moveit_config_builder.trajectory_execution(
            get_file_path(package, ["config"], "moveit_controllers.yaml")
        )
        moveit_config_builder.moveit_cpp(
            get_file_path(package, ["config"], "planning_pipeline.yaml")
        )
        moveit_config_builder.sensors_3d(
            get_file_path(package, ["config"], "sensors_3d.yaml")
        )
        moveit_config = moveit_config_builder.to_moveit_configs()

        # Define namespace dependent parameters:
        moveit_config.sensors_3d["depth_image"]["image_topic"] = (
            f"/{namespace}/octomap/depth_image"
        )
        moveit_config.sensors_3d["depth_image"]["filtered_cloud_topic"] = (
            f"/{namespace}/octomap/filtered_points"
        )

        # adapt robot_description with prefix:
        add_prefix_in_robot_description(robot_description, namespace)
        moveit_config.robot_description = robot_description

        # adapt robot_description_semantic with prefix:
        robot_description_semantic = get_robot_description(srdf_path, semantic=True)
        add_prefix_in_robot_description_semantic(robot_description_semantic, namespace)
        moveit_config.robot_description_semantic = robot_description_semantic

        Moveit.configurations[namespace] = moveit_config
        Moveit.servo_configurations[namespace] = {"moveit_servo": servo_config}


def add_prefix_in_robot_description(description: dict, prefix: str) -> None:
    """Add a prefix to all links in the robot description.

    Args:
        description (dict): The robot description dictionary.
        prefix (str): The prefix to add to each link.
    """
    xml_dict = xmltodict.parse(description["robot_description"])

    for link in xml_dict["robot"]["link"]:
        name = link["@name"]
        link["@name"] = f"{prefix}/{name}"
    for joint in xml_dict["robot"]["joint"]:
        parent = joint["parent"]["@link"]
        child = joint["child"]["@link"]
        joint["parent"]["@link"] = f"{prefix}/{parent}"
        joint["child"]["@link"] = f"{prefix}/{child}"

    description["robot_description"] = xmltodict.unparse(xml_dict)


def add_prefix_in_robot_description_semantic(description: dict, prefix: str) -> None:
    """Add a prefix to all links in the semantic robot description.

    Args:
        description (dict): The semantic robot description dictionary.
        prefix (str): The prefix to add to each link.
    """
    xml_dict = xmltodict.parse(description["robot_description_semantic"])
    ee_parent_link = xml_dict["robot"]["end_effector"]["@parent_link"]
    xml_dict["robot"]["end_effector"]["@parent_link"] = f"{prefix}/{ee_parent_link}"
    for group in xml_dict["robot"]["group"]:
        if "link" in group:
            group["link"]["@name"] = f"{prefix}/{group['link']['@name']}"
    for disable_collision in xml_dict["robot"]["disable_collisions"]:
        link1 = disable_collision["@link1"]
        link2 = disable_collision["@link2"]
        disable_collision["@link1"] = f"{prefix}/{link1}"
        disable_collision["@link2"] = f"{prefix}/{link2}"

    description["robot_description_semantic"] = xmltodict.unparse(xml_dict)
