<!--
SPDX-FileCopyrightText: Alliander N. V.

SPDX-License-Identifier: Apache-2.0
-->

# Grasping

Grasping is an important but challenging skill of a robot. To integrate this skill into our robots, we require a tool that can define the best grasp position for our robot gripper, to grasp an object of interest.

## Grasp Generation Methods

We define three different strategies to define the best grasp position:

### Logic based

The logic based strategy defines 'rules' that should lead to grasping an object successfully. This strategy can be useful when the object to grasp is constant. For example: to grasp bricks, one might introduce rules like 'grasp the brick as much centered as possible' and 'place the fingers always on the long sides of the brick'. The great disadvantage of this method is that it doesn't scale when the objects to grasp differ or are unknown. It is impossible to define rules for every possible object.

### Generation based

The generation based strategy uses a trained AI model to sample grasp poses on a given object, followed by a scoring and filtering to select the best poses. Creation of the required models is complex and very computational expensive, but fortunately are some models shared, for example with research papers. Two popular models published on GitHub are [GraspNet](https://github.com/graspnet/graspnet-baseline) ([AnyGrasp](https://arxiv.org/pdf/2212.08333)) and [GraspGen](https://github.com/NVlabs/GraspGen) ([paper](https://arxiv.org/pdf/2507.13097)).

### Vision Language Action based

The vision language action based strategy requires an AI model that integrates vision, language and actions to execute tasks. With these models, one could theoretically give a command like 'pull the red handle'. A model like [OpenVLA](https://github.com/openvla/openvla) or [DexGraspVLA](https://github.com/Psi-Robot/DexGraspVLA) should create an action list to bring the visioned state to the commanded state. This is a continuous process of performing actions and checking the resulting visual feedback, trying to get closer to the commanded state.

## Integration of a Generation Based Model

Since the logic-based strategy is not scalable, while VLA is still very complex and controls the whole action strategy of the robot, we decided to focus on the generation based strategy. To use an existing generation based method, we need to integrate it in our robot system. Since there are many generation based models and development is still very active, a modular way to integrate a model is desired.

### Architecture of Generation Based models

Inspection of the two popular models of GraspNet and GraspGen show many similarities:

:::{mermaid} ../diagrams/generation_based_models.mmd
:::

Both methods provide demo code. GraspNet only offers a demo where an RGBD image is used as input. GraspGen offers several demo scripts, where the input can be a point cloud, a mesh or an RGBD image. All demos of GraspGen and the demo of GraspNet first convert the input to a point cloud and use a mask to isolate the point cloud of the object of interest.

We can therefore conclude that the actual input of the models is an isolated point cloud of the object to grasp. Both models generate grasp poses using the isolated point cloud. Finally, both methods also offer a collision detection method, to check gripper collision with the original point cloud for all generated grasps.

### Modular Integration

To integrate a model in a modular way, we need to define the input and the output. Since both GraspNet and GraspGen eventually use a point cloud of the object of interest to sample a list of grasp poses, these are respectively our defined input and output.

Instead of using the model functions to create this point cloud from another data format, we can create this functionality as a separate function in our system. This gives us the flexibility to create a more detailed point cloud, for example from multiple RGBD images. This also makes us (for this step) independent of the chosen model, which makes it easier to switch between models.

To use the grasp generation of a model, some wrapper software needs to be created. This wrapper software can be similar to the demo code of a model, with the difference that it will only use the grasp generation function, respecting our defined input and output.

The collision detection functionality should also be a separate function of our own system, for the same reason that we have more control over it and makes us independent of a chosen grasp generation model.

:::{mermaid} ../diagrams/grasping_model_integration.mmd
:::

### Software Architecture

To achieve the described modular integration, several functionalities need to be developed:

- create_point_cloud
- generate_grasps_wrapper
- collision_filtering

To share data between these functionalities, we can use the ROS architecture. We could consider a GraspManager (similar to our MoveitManager), that manages all the grasp related functionalities. The MoveitManager can use an instance of the GraspingManager, since movement towards the generated grasp poses will be generated using MoveIt. To achieve this, the GraspingManager should be written as a C++ class/library, since our MoveitManager is also written in C++.

The Generation based models are however written in Python. This means that the GraspModelWrapper should also be written in Python. We can define the GraspModelWrapper as an individual ROS node that can communicate with the other functionalities of the GraspingManager using ROS topics, services or actions.

:::{mermaid} ../diagrams/grasping_software_architecture.mmd
:::
