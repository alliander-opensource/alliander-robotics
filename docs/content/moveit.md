<!--
SPDX-FileCopyrightText: Alliander N. V.

SPDX-License-Identifier: Apache-2.0
-->

# Moveit

According to the official [website](https://moveit.picknik.ai/main/index.html):

"*MoveIt 2 is the robotic manipulation platform for ROS 2 and incorporates the latest advances in motion planning, manipulation, 3D perception, kinematics, control, and navigation.*"

This documentation shows Moveit components that are used in this repository, sometimes with some additional explanation about implementation choices.

## Why do we use Moveit?

Moveit offers an extensive platform of motion planning software and tools. We use these motion planners to control our robot arm. Since a robot arm can easily contain 6 or more joints, motion planning is a complex multi-dimensional task. Usually, we are interested in planning a motion such that:

- The end-effector moves from a pose A to a pose B in cartesian space.
- Obstacle collisions are avoided.
- Singularities are avoided.
- Possible additional constraints are respected, like linear motion.

Besides the planning, also visualization of the planned path can be very useful. All these tasks can be done with Moveit.

### MoveGroup, C++ or Python?

Moveit can be used in different ways. The easiest is to use the MoveGroup interface, since it provides easy functionality for most operations of Moveit. Another benefit is that we can also control Moveit using a plugin in Rviz, which will be discussed later in more detail. For these reasons, we also make use of the MoveGroup interface.

If more complexity is required, one can also use the C++ API of Moveit. This skips a layer of ROS, which leads to faster performances. Some of the C++ API is also available in the Python API. However, based on our experience, the Python functionalities and documentation are very minimal and we therefore advise to use the MoveGroup interface or the C++ API. More information about the differences can be found [here](https://moveit.picknik.ai/main/doc/examples/examples.html).

## How do we use Moveit?

As mentioned before, we make use of the MoveGroup interface. One can start the `move_group` as a ros node of the `moveit_ros_move_group` package. However, the node requires many parameters to start and function correctly. Therefore, we always start the node using the launch file `moveit.launch.py`, located in our package `alliander_moveit`, where we can easily pass the configuration parameters. Moveit configurations are defined in a separate package, which can be created for a desired robot arm using the [Moveit setup assistant](https://moveit.picknik.ai/main/doc/examples/setup_assistant/setup_assistant_tutorial.html). For example, for the Franka robot arm, we created the `alliander_franka_moveit_config` package.

## Control in Rviz

If a robot and the move_group are launched correctly, we can load the *MotionPlanning* plugin. This should visualize the orange goal state of the robot, which can be adapted by dragging around the ball-marker located at the end-effector. Next, we can plan a motion towards the goal and execute it:

:::{video} ../vid/moveit/rviz.mp4
:width: 100%
:::

## Moveit Manager

Using the tool in Rviz, we can simply move the robot. However, our goal is to make the robot work autonomously and therefore we also need another way to interact with Moveit. To do this, we have created the `moveit_manager` node, located in the `alliander_moveit` package. The `moveit.launch.py` launch file discussed earlier launches both the `move_group` node and our `moveit_manager` node. Our moveit_manager interacts with the move_group, similarly as that the plugin in Rviz can interact with the move group.

We have developed functionality to plan movements to a pose or to predefined configurations, to visualize markers in Rviz, to add or remove obstacles or to execute sequences of actions, for example to pick something at a given pose and drop it at another pose. All these functionalities are exposed as ROS services, and can therefore easily be integrated in a broader autonomous task that the robot will perform. This video shows an example where multiple actions are performed using Moveit to grab a brick and drop it at the side of the robot:

:::{video} ../vid/moveit/manager.mp4
:width: 100%
:::

The next video shows another example, where an collision object gets defined. Moveit will try to plan another movement to reach the goal without obstacle collision:

:::{video} ../vid/moveit/obstacle_avoidance.mp4
:width: 100%
:::

## Planners

As you can see in the video above, the two paths to move around the object are very different. The motion plan that Moveit will find is highly dependent on the type of planner that is used. More information about different planners can be found [here](https://moveit.ai/documentation/planners/). At the time of writing, we have implemented functionality for Moveit's default [OMPL planner](https://moveit.picknik.ai/main/doc/examples/ompl_interface/ompl_interface_tutorial.html) in combination with the [BIO IK](https://github.com/PickNikRobotics/bio_ik) inverse kinematics plugin and the [Pilz Industrial Motion Planner](https://moveit.picknik.ai/main/doc/how_to_guides/pilz_industrial_motion_planner/pilz_industrial_motion_planner.html). Pilz Industrial Motion Planner can be used to let Moveit generate a motion plan where the end-effector moves over a linear or circular path from one pose to another. This can be very useful when it is desired that the end-effector move over a predictable path. The next video shows the difference when moving between a high pose anbd a low pose by first using the default OMPL planner and next using the linear planner from Pilz:

:::{video} ../vid/moveit/planners.mp4
:width: 100%
:::

## Gamepad Control

Besides the interaction with Moveit using the plugin in Rviz and our developed Moveit Manager node, we also support direct interaction using a gamepad. To achieve this, we make use of the `servo_node` from the `moveit_servo` package. This node, provided by Moveit, facilitates realtime control of the robot arm, based on the input of the gamepad. More information can be found [here](https://moveit.picknik.ai/main/doc/examples/realtime_servo/realtime_servo_tutorial.html).

The `moveit.launch.py` launch file discussed earlier launches also the `servo_node`, next to the `move_group` node and our `moveit_manager` node. The servo_node does not use the move_group, but communicates directly with Moveit. When a X-Box controller is connected, we can press the A-button to start gamepad control for the arm:

:::{video} ../vid/moveit/gamepad.mp4
:width: 100%
:::

As long as this gamepad control is activated, we cannot use Moveit via the Rviz plugin or our moveit_manager node, since this is directly overruled by the gamepad commands. One can disable the gamepad-control by pressing the X-button on the X-box gamepad.
