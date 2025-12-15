# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

from launch import LaunchContext, LaunchDescription
from launch.actions import OpaqueFunction
from rcdt_utilities import launch_utils
from rcdt_utilities.register import Register, RegisteredLaunchDescription
from rcdt_utilities.ros_utils import get_file_path


def launch_setup(context: LaunchContext) -> list:
    """The launch setup.

    Args:
        context (LaunchContext): The launch context.

    Returns:
        list: The actions to start.
    """
    simulation = True
    namespace = "franka"

    state_publisher = launch_utils.state_publisher_node(
        namespace=namespace,
        platform="franka",
        xacro="franka.urdf.xacro",
        xacro_arguments={"simulation": str(simulation), "namespace": namespace},
    )

    map_link = launch_utils.static_tf_node(
        parent_frame="map",
        child_frame=f"{namespace}/world" if simulation else f"{namespace}/base",
    )

    controllers = RegisteredLaunchDescription(
        get_file_path("rcdt_franka", ["launch"], "controllers.launch.py")
    )

    gripper = RegisteredLaunchDescription(
        get_file_path("rcdt_franka", ["launch"], "gripper_services.launch.py"),
        launch_arguments={"namespace": "franka"},
    )

    return [
        Register.on_start(state_publisher, context),
        Register.on_start(map_link, context),
        Register.group(controllers, context),
        Register.group(gripper, context),
    ]


def generate_launch_description() -> LaunchDescription:
    """Generate the launch description.

    Returns:
        LaunchDescription: The launch description.
    """
    return LaunchDescription(
        [
            OpaqueFunction(function=launch_setup),
        ]
    )
