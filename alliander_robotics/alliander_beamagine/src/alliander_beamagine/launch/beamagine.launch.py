# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

from alliander_utilities.config_objects import Beamagine
from alliander_utilities.launch_argument import LaunchArgument
from alliander_utilities.launch_utils import SKIP, state_publisher_node, static_tf_node
from alliander_utilities.register import Register, RegisteredLaunchDescription
from alliander_utilities.ros_utils import get_file_path
from launch import LaunchContext, LaunchDescription
from launch.actions import OpaqueFunction
from launch_ros.actions import Node

platform_arg = LaunchArgument("platform_config", "")


def launch_setup(context: LaunchContext) -> list:
    """The launch setup.

    Args:
        context (LaunchContext): The launch context.

    Returns:
        list: The actions to start.
    """
    beamagine_config = Beamagine.from_str(platform_arg.string_value(context))

    state_publisher = state_publisher_node(
        namespace=beamagine_config.namespace,
        platform="beamagine",
        xacro="l3cam.urdf.xacro",
        xacro_arguments={
            "namespace": beamagine_config.namespace,
            "parent": "" if beamagine_config.parent.link else "world",
            "use_sim": str(beamagine_config.simulation),
        },
    )

    parent = beamagine_config.parent
    static_tf = static_tf_node(
        parent_frame=f"{parent.namespace}/{parent.link}" if parent.link else "map",
        child_frame=f"{beamagine_config.namespace}/{parent.connects_to}",
        position=beamagine_config.position,
        orientation=beamagine_config.orientation,
    )

    hardware = RegisteredLaunchDescription(
        get_file_path("alliander_beamagine", ["launch"], "hardware.launch.py"),
        {"platform_config": beamagine_config.to_str()},
    )

    convert_32fc1_to_16uc1 = Node(
        package="alliander_utilities_depth_camera",
        executable="convert_32FC1_to_16UC1",
        namespace=beamagine_config.namespace,
    )

    return [
        Register.on_start(state_publisher, context),
        Register.on_start(static_tf, context),
        Register.on_start(convert_32fc1_to_16uc1, context)
        if beamagine_config.simulation
        else SKIP,
        Register.group(hardware, context) if not beamagine_config.simulation else SKIP,
    ]


def generate_launch_description() -> LaunchDescription:
    """Generate the launch description.

    Returns:
        LaunchDescription: The launch description.
    """
    return LaunchDescription(
        [
            platform_arg.declaration,
            OpaqueFunction(function=launch_setup),
        ]
    )
