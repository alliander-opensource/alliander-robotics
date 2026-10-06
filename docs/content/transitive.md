<!--
SPDX-FileCopyrightText: Alliander N. V.

SPDX-License-Identifier: Apache-2.0
-->

# Transitive

According to the official website:

"*Transitive is an open-source framework for full-stack robotics. It is designed to make it easy to create capabilities that seamlessly connect robot, cloud, and web front-ends including a dynamically updating shared data model.*"

It provides software to setup real-time data synchronization between our robots and the cloud. Furthermore does it provide capabilities: modular packages that add web-based features like video streaming or teleportation. This documentation shows how
Transitive can be used in combination with our software stack.

## Agent

To connect a robot to the online Transitive portal, one requires to run a Transitive agent on the robot. To do this, one can simply use the `transitive_agent` docker container in our repository. This container expects a `transitive.env` file in the home directory of the host device with the following content:

```env
TR_INSTALL_HASH=<unique_robot_id_in_fleet>
TR_USERID=<user_id_transitive_account>
TR_ROBOT_TOKEN=<token_from_transitive_account>
TR_DISPLAYNAME=${TR_INSTALL_HASH}
TR_LABELS=<optional_labels_separated_by_comma>
```

Create the file if it doesn't exist yet, fill the required variables with a unique id for the robot. Next, one can start the container:

```bash
cd alliander_robotics/transitive/agent
docker compose up -d
```

- For debugging purposes, one can also start the container without the `-d` flag, so that the terminal stays attached to the container.
- The container contains a ROS2 installation. Since `network_mode: host` is specified in the compose file, the agent can communicate with all the ROS2 nodes from the other containers we start on our robot.
- The compose file specifies `privileged: true`, since this is a requirement to [run the agent](https://transitiverobotics.com/docs/guides/installing_in_docker/#run) as it uses linux namespaces to sandbox capabilities.
- The compose file specifies `restart: unless-stopped`, which means that this container should automatically restart, for example after a reboot. Only when stopped manually, the container does not restart, which is desirable when using the agent on a laptop to test with simulation.

## Portal

To monitor the robots running a Transitive agent, one can visit the online portal at <https://portal.transitiverobotics.com/>.
After logging, the **Devices** page is shown where one can select a robot in the fleet. After selecting a device, the device page will be opened where capabilities can be added to the robot.

## Web UI

One can embed the capabilities added in the portal to a web page. Embedding allows to set specific settings for the capability. Right now, we have a very basic Web UI that can be served locally using Vite. To do this, one can simply use the `transitive_ui` docker container in our repository. This container expects a `transitive.env` file in the home directory of the host device with the following content:

```env
VITE_USERID=${TR_USERID}
VITE_JWT_SECRET=<JWT secret in our Transitive account>
```

Fill the required variables. Next, one can start the container:

```bash
cd alliander_robotics/transitive/ui
docker compose up
```

The Web UI is locally served using Vite and the terminal shows the address to open the web page.

### Waypoints and missions
Inside the Web UI is a map on which you can place waypoints. The placed waypoints will be shown on the Waypoints panel on the right. You can move (drag them on the map), remove (right-click on the map or X on the panel), and re-order (the arrows on the panel) waypoints. Separate buttons allow you to Save waypoints to a JSON file on your device, or to Load waypoints in from a JSON file that you upload.

The Mission panel above it enables you to Start, Stop, Pause, and Resume missions. Resume's current implementation finds the closest waypoint to the robot, and removes all waypoints before that. The robot will then resume its mission from this closest waypoint. 
Make sure to correctly fill out the Namespace for your robot topic.
