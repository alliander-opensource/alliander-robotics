<!--
SPDX-FileCopyrightText: Alliander N. V.

SPDX-License-Identifier: Apache-2.0
-->

# Platforms

This page describes the use of the different platforms we support.

The general rule we apply for assigning IP addresses follows the following numbering order:

> 1 - Router \
2 - Low-level computer (Raspberry Pi) \
3 - High-level computer \
4 - Additional component (e.g. Franka Arm) \
5 - LiDAR

So for example, if we connect the Ouster LiDAR to the Lynx, we assign the Ouster with IP address `10.15.20.5`.

## Franka

![Franka](../img/franka/franka.png)

### Simulation Franka

A Franka arm can be launched in simulation by creating a configuration with an *Arm* of type *franka*.

### Hardware Franka

- The robot needs to be connected with it's control box.
- Flip the switch on the control box to start the robot.
- An ethernet cable should connect the control box with the network.
- By default, we connect the control box with the router of the Panther.
- The web interface can be reached on the statically assigned address: `10.15.20.4`.

In the web-interface, settings can be changed and the joints can be (un)locked. The mode can also be changed to the required FCI mode.

## UR

![UR](../img/ur/ur.png)

### Simulation UR

A UR arm can be launched in simulation by creating a configuration with an *Arm* of type *ur*.

### Hardware UR

We have a [UR7e](https://www.universal-robots.com/download/manuals-e-seriesur-series/user/ur7e/522/user-manual-ur7e-sw-522-english-international-en/) arm with the [OEM DC Control Box](https://www.universal-robots.com/download/manuals-e-seriesur-series/installation-guides/oem-control-box/oem-control-box-installation-guide-english-en-e-seriesur-series/), so that it is possible to directly the power the UR arm with one of our vehicle platforms. This OEM version does not contain a Teach Pendant and a correct DC power supply is required. We built the following circuit to power the control box:

| ![circuit](../img/ur/circuit.png) | ![diagram](../img/ur/diagram.png) |
| - | - |

If desired, one can connect a display before startup using the mini display port, to visualize the control box interface. Now start the control box:

- The robot needs to be connected with its control box.
- Use the laboratory power supply or a vehicle platform to provide a DC source of 48V, 10A.
- Flip the main switch on the control box (0 -> 1) to power the control box.
- An ethernet cable should connect the control box with the network.
- Start the control box by pressing the small button in the red mount.

The control box will start, which can take two minutes, indicated by a green led on the control box. Since [remote control](https://docs.universal-robots.com/Universal_Robots_ROS2_Documentation/doc/ur_client_library/doc/setup/robot_setup.html#robot-setup) is enabled, the arm can be started directly from our code using [headless mode](https://docs.universal-robots.com/Universal_Robots_ROS2_Documentation/doc/ur_robot_driver/ur_robot_driver/doc/operation_modes.html):

- Use a correct manual ip address for the host device to communicate with the control box (which has `172.16.0.2` by default).
- You can test the connection using `ping` and the `alliander_robotics/alliander_ur/dashboard.py` tool.
- Run a configuration of the UR arm, the arm should start automatically, indicated by a green led on the control box.
- You can *power off* the arm and *shutdown* the control box using the `dashboard.py` tool.

In case the arm has entered a protective stop:

1. Unlock using the `dashboard.py` tool.
2. Attach to the UR docker container and run `ros2 service call /ur/io_and_status_controller/resend_robot_program std_srvs/srv/Trigger {}`.

## Panther

![Panther](../img/panther/panther.png)

### Simulation Panther

A Panther vehicle can be launched in simulation by creating a configuration with a `Vehicle` of type `Panther`. Note that the E-Stop is triggered by default and needs to be released before driving is possible. This can be done by a service call:

```bash
ros2 service call /panther/hardware/e_stop_reset std_srvs/srv/Trigger {}
```

### Hardware Panther

- Enable the battery (switch at the front of the robot).
- Start the robot (press red power button).
- Wait until the [E_STOP animation](https://husarion.com/manuals/panther/software/ros2/robot-management/#led-animations) is played
- Release hardware stop (rotate red emergency button if it was pressed).
- Start the Logitech gamepad:
  - press Logitech button.
  - press *mode* button if mode light is on (should be off).
  - put the switch at the back on *X*.
- Remove the E_STOP by *Left Trigger + A* on the gamepad.
- You can drive by pressing *Left Button* and use the two joysticks.
- You can enable the E_STOP by pressing *B*.
- See [this](https://husarion.com/manuals/panther/software/ros2/robot-management/#gamepad) for more information about gamepad control.

One can enable the high voltage system of the Panther (for example to power an Arm) using a service call:

```bash
ros2 service call /panther/hardware/aux_power_enable std_srvs/srv/SetBool "{data: true}"
```

The robot can be shut down as follows:

- Shut down the robot (hold red button next to battery switch till it starts blinking).
- Wait until all lights are off.
- Disable the battery (switch at the front of the robot)

### Configuration Panther

When the Panther is started, two WiFi networks (*Panther_<serial_number>* and *Panther_5G_<serial_number>*) should be available. One can connect with one of the WiFi networks or connect using a ethernet cable directly to the Teltonika. After connecting, it should be possible to ssh into all three computers.

**Teltonika RUTX11:**
\
This is an industrial router. The *Raspberry Pi 4* and *Lenovo ThinkStation P360* are connected to the *Teltonika* by Ethernet. Also the *Velodyne Lidar* and is connected to the *Teltonika* by Ethernet. A [combo antenna](https://teltonika-networks.com/products/accessories/antenna-options/combo-mimo-mobilegnsswi-fi-roof-sma-antenna) (the black dome) is also connected, which enables the *Teltonika* to obtain a GPS location.

**Raspberry Pi 4 :**
\
The *Raspberry Pi 4* is built in the front of the Panther and not directly accessible. Two Docker images are pre-installed: a [docker image](https://hub.docker.com/r/husarion/panther) of the [panther_ros](https://github.com/husarion/panther_ros) repository and a [docker image](https://hub.docker.com/r/husarion/joy2twist) of the [joy_to_twist](https://github.com/husarion/joy2twist) repository. Both images are started automatically when the robot starts, as do all docker images installed on the Pi. The first image runs all the required software to use the robot, like motor control and led control. The second image enables gamepad control with the Logitech gamepad shipped with the robot, when the USB receiver is connected to the USB port at the front of the robot.

We have also cloned the [nmea-gps-docker](https://github.com/husarion/nmea-gps-docker/tree/ros2) repository with a docker that enables use of GPS in ROS. This docker images gets started automatically as well when the the Panther starts. For more information about the use of this docker, see the Sensors section.

**Lenovo ThinkStation P360**
\
The *Lenovo ThinkStation P360* is a powerful computer, used to handle the camera stream. We can run our docker image on this built in computer.

## Lynx

![Lynx](../img/lynx/lynx.png)

### Simulation Lynx

A Lynx vehicle can be launched in simulation by creating a configuration with a `Vehicle` of type `Lynx`.

### Hardware & Configuration Lynx

This section is equivalent to the [Hardware Panther](#hardware-panther) and [Configuration Panther](#configuration-panther) sections, except for the namespace here being `lynx` and the *Lenovo ThinkStation P360* will be replaced with a different computer.

## Ewellix

![Ewellix](../img/ewellix/ewellix.png)

### Simulation Ewellix

An Ewellix lift can be launched in simulation by creating a configuration with an *Lift* of type *ewellix*. One can control the lift by publish a command on the `lift_position_controller/commands` topic.

### Hardware Ewellix

One can use an Ewellix lift by connecting it with the host device using USB. One can control the lift by publish a command on the `lift_position_controller/commands` topic.

## Realsense

![Realsense](../img/realsense/realsense.png)

### Simulation Realsense

A Realsense camera can be launched in simulation by creating a configuration with an *Camera* of type *realsense*.

### Hardware Realsense

One can use a Realsense by connecting it with the host device using USB.

## Seek Thermal

![SeekThermal](../img/seekthermal/seekthermal.png)

### Simulation Seek Thermal

A Seek Thermal camera can be launched in simulation by creating a configuration with a *ThermalCamera* of type *seekthermal*.

### Hardware Seek Thermal

To use the Seek Thermal camera, connect it to a PoE injector's *OUT* port. A PoE injector is shipped as an accessory with the G300, and can be plugged into a power socket. Connect the *IN* port to your device, define a manual internet connection with an ip address in the `169.254.63.X` range (not 169.254.63.63, since this is the defautl ip address of the sensor), then launch the *alliander_seekthermal* container. If you get a connection error, you may need to press the *RESET* pin on the G300 while it is connected to your device in order for the G300 to follow your device's network rules.

## ZED

![ZED](../img/zed/ZED.png)

### Simulation Zed

A ZED camera can be launched in simulation by creating a configuration with an *Camera* of type *zed*.

### Hardware Zed

A ZED camera can be used by connecting it to the host device via USB. To allow non-root users to access the camera, UDEV rules must be installed on the host machine. The required script can be found [here](https://gist.github.com/adujardin/2d5ce8f000fc6a7bd40bee2709749ff8).

## Ouster

![Ouster](../img/ouster/ouster_os1.png)

### Simulation Ouster

An Ouster lidar can be launched in simulation by creating a configuration with a *Lidar* of type *Ouster*.

### Hardware Ouster

**Network settings:**
\
When using the Ouster lidar, make sure that the IP-address of the host device (where the Ouster node is running) is set correctly in the settings of the Teltonika router. One can assign a static IP address to the Ouster via the Teltonika interface. In case of the Husarion vehicles, this interface is reachable via `http://10.15.20.1/`, and the static IP address should be set to `10.15.20.5` as number 5 is reserved for LiDARs.

Additionally, it is important to assign the correct UDP destination IP address for the Ouster LiDAR. This can both be done via the Ouster's configuration interface at `http://os-{serial_number}.local/`, or it can be done via the launch file of the Ouster (`ouster.launch.py` in the `alliander_ouster` package).

*Note:* If the firewall is enabled in Ubuntu, communication with the LiDAR is most likely blocked. Unblock it by allowing the IP-address of the LiDAR:

```bash
sudo ufw allow to {IPv4_address}
sudo ufw allow from {IPv4_address}
```

**ROS2 setup:**
\
The [Ouster driver](https://github.com/ouster-lidar/ouster-ros/tree/ros2) runs as a [LifeCycle node](https://design.ros2.org/articles/node_lifecycle.html), meaning that once created, the node starts in an `Unconfigured` state. It needs to be `configured` and `activated` to start the driver.

Find all of the connected Ouster's information at `http://os-{serial_number}.local/`, where the following parameters for the driver node can be found:

- `sensor_hostname`: Dashboard > System Information > IPv4 *(Remove the prefix length)*
- `udp_dest`: Dashboard > System Status > Web Client Address

## Velodyne

![Velodyne](../img/velodyne/velodyne.png)

### Simulation Velodyne

A Velodyne lidar can be launched in simulation by creating a configuration with a *Lidar* of type *velodyne*.

### Hardware Velodyne

When using the Velodyne lidar, make sure that the IP-address of the host device (where the velodyne node is running) is set correctly in the settings. One can edit the settings of the velodyne using a web interface on it's IP-adress.

| ![Velodyne settings](../img/velodyne/velodyne_settings.png) | ![Teltonika settings](../img/teltonika/teltonika_settings.png) |
|-------------------------------------------------------------|----------------------------------------------------------------|

## Xsens IMU

![Xsens](../img/xsens/xsens.png)

### Simulation Xsens

An Xsens IMU can be launched by creating a configuration with an *IMU* of type *xsens*.

### Hardware Xsens

When using the Xsens IMU, make sure that the IMU shows up on your device (use *lsusb* to check) and that the Docker container runs with *privileged: true* (standard in our repo).

## GPS

### U-Blox GPS

#### Hardware X20P

If using multiple GPS devices, e.g. in a rover-base configuration, correct device enumeration may need some extra configuration. The GPS library ![ublox-dgnss](https://github.com/aussierobots/ublox_dgnss.git) diffentiates between X20P devices based on the `DEVICE_SERIAL_STRING`, which can be found by running `python3 ublox_serial.py list` in `alliander_ublox/src/alliander_ublox/scripts/` with a U-Blox GPS attached (works better if you are in the `allianderrobotics/gps` Docker container with `sleep infinity`).
The value is supposed to be unique for each device, set during construction in the factory. This is not always the case however -- sometimes it just reads 0.

In that case, you have two options:

- set it with `python3 ublox_serial.py set-persistent <bus-port> <string>`. Remove and plug the device in again for the change to take effect. You can do this from a Docker container (make sure to add the `privileged` flag for hardware access!): `docker run -it --rm --privileged allianderrobotics/gps bash`.
- set it in u-center 2 on Windows, under `Device Configuration > USB > SERIAL_NO_STR0`. Make sure to `Set` and `Send` to RAM, BBR, and flash.

### Teltonika GPS

![Teltonika](../img/teltonika/nmea.png)

#### Simulation Teltonika

A Teltonika GPS can be launched in simulation by creating a configuration with a *GPS* of type *teltonika*.

#### Hardware Teltonika

When using the Teltonika GPS, make sure that the IP-address of the host device (where the nmea node is running) is set correctly in the settings. One can edit the settings of the Teltonika using a web interface on it’s IP-adress.

## Beamagine L3Cam

![Beamagine](../img/beamagine/beamagine.png)

### Simulation Beamagine

A Beamagine lidar can be launched in simulation by creating a configuration with the *Beamagine* type.

### Hardware Beamagine

When using the Beamagine lidar, make sure that the network buffer sizes are increased. This can be checked using:

```bash
sudo sysctl 'net.core.rmem_max' # should be 268435456
sudo sysctl 'net.core.rmem_default' # should be 268435456
sudo sysctl 'net.core.netdev_max_backlog' # should be 5000
```

Update the buffer size with the following commands:

```bash
sudo sh -c "echo 'net.core.rmem_default=268435456' >> /etc/sysctl.conf"
sudo sh -c "echo 'net.core.rmem_max=268435456' >> /etc/sysctl.conf"
sudo sh -c "echo 'net.core.netdev_max_backlog=5000' >> /etc/sysctl.conf"
sudo sysctl -p
```

The Beamagine requires a 12V 5A power supply. Connect the ethernet cable to the host device and define a manual network connection with MTU of 9000 (identity page) and an ip address of `192.168.0.10`.

## RobotIQ 3-finger gripper

![RobotIQ](../img/robotiq/robotiq.png)

### Simulation RobotIQ

A RobotIQ gripper can be launched in simulation by creating a configuration with a Gripper of type *Robotiq*. After launching the RobotIQ configuration, one can control the gripper by sending one of the supported commands (activate, reset, open, close, wide-open, wide-close, pinch-open, pinch-close) to the `/robotiq/gripper_controller/action` action server as a string. For example:

```bash
ros2 action send_goal /robotiq/gripper_controller/action alliander_interfaces/action/StringAction '{text: close}'
```

### Hardware RobotIQ

When using the RobotIQ gripper, connect the power cable to a 24V, 1.5A power source and connect the communication cable to the ethernet port of the host device. One the host device, configure the wired connection to manually use an ip-address in the `192.168.1` range, for example `192.168.1.2`. The gripper uses the `192.168.1.11` address by default. After launching the RobotIQ configuration, one can control the gripper by sending one of the supported commands (activate, reset, open, close, wide-open, wide-close, pinch-open, pinch-close) to the `/robotiq/gripper_controller/action` action server as a string. The status of the gripper is published on the `/robotiq/status` topic as a JSON string and can be continuously visualized in the terminal using our `print_json` utility node: `ros2 run alliander_utilities print_json.py --ros-args -p topic:=/robotiq/status`.

## Apriltag

![Apriltag](../img/apriltag/apriltag.png)

### Simulation Apriltag

One can define an apriltag as a 'special' platform. Since an apriltag is not a sensor or a robot, no robot_description topic is published and therefore no model is visible in Rviz. Instead, a 3d-model of the apriltag is created and spawned into Gazebo when simulation is used. Since the `Apriltag` platform class inherits from the `Platform` base class, one can still link the apriltag as a child to another (moving) platform. Note that we only support apriltags (and not aruco markers) as apriltags are commonly used in ROS2 (for example by Nav2) and only the `36h11` family, as only these tags are [supported](https://nvidia-isaac-ros.github.io/repositories_and_packages/isaac_ros_apriltag/isaac_ros_apriltag/index.html#ros-parameters) by `isaac_ros_apriltag` on GPU. If a configuration with an apriltag and a camera is launched, the `alliander_apriltag` container is launched automatically.

### Hardware Apriltag

When launching a hardware configuration with at least a camera and apriltag definition, the `alliander_apriltag` container is still launched automatically. The `apriltag_manager` node will automatically publish the pose of the detected markers on the topic defined in the `Apriltag` platform object.
