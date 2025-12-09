<!--
SPDX-FileCopyrightText: Alliander N. V.

SPDX-License-Identifier: Apache-2.0
-->

# Platforms

This page describes the use of the different platforms we support.

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

In the web-interface, settings can be changed and the joints can be (un)locked. The mode can also be changed to the required FCI mode. It is also possible to unlock and activate the FCI entirely from the command line by dropping a `.env` file in your workspace root:

```text
# .env
FRANKA_USERNAME=your-username
FRANKA_PASSWORD=your-password
```

This functionality is based on [jk-ethz/franka\_lock\_unlock](https://github.com/jk-ethz/franka_lock_unlock).
We created a fork with robot-specific enhancements: [https://github.com/alliander-opensource/franka\_lock\_unlock.git](https://github.com/alliander-opensource/franka_lock_unlock.git)

## Panther

![Panther](../img/panther/panther.png)

Regarding all vehicles, the general rule we apply for assigning IP addresses follows the following numbering order:

> 1 - Router \
2 - Low-level computer (Raspberry Pi) \
3 - High-level computer \
4 - Additional component (e.g. Franka Arm) \
5 - LiDAR

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

This section is equivalent to the [Hardware Panther](#hardware-panther) and [Configuration Panther](#configuration-panther) sections, except for the namespace here being `lynx` and the _Lenovo ThinkStation P360_ will be replaced with a different computer.

## Realsense

![Realsense](../img/realsense/realsense.png)

### Simulation Realsense

A Realsense camera can be launched in simulation by creating a configuration with an *Camera* of type *realsense*.

### Hardware Realsense

One can use a Realsense by connecting it with the host device using USB.

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

Additionally, it is important to assign the correct UDP destination IP address for the Ouster LiDAR. This can both be done via the Ouster's configuration interface at `http://os-{serial_number}.local/`, or it can be done via the launch file of the Ouster (`ouster.launch.py` in the `rcdt_sensors` package).

_Note:_ If the firewall is enabled in Ubuntu, communication with the LiDAR is most likely blocked. Unblock it by allowing the IP-address of the LiDAR:

```bash
sudo ufw allow to {IPv4_address}
sudo ufw allow from {IPv4_address}
```

**ROS2 setup:**
\
The [Ouster driver](https://github.com/ouster-lidar/ouster-ros/tree/ros2) runs as a [LifeCycle node](https://design.ros2.org/articles/node_lifecycle.html), meaning that once created, the node starts in an `Unconfigured` state. It needs to be `configured` and `activated` to start the driver.

Find all of the connected Ouster's information at `http://os-{serial_number}.local/`, where the following parameters for the driver node can be found:
- `sensor_hostname`: Dashboard > System Information > IPv4 _(Remove the prefix length)_
- `udp_dest`: Dashboard > System Status > Web Client Address


## Velodyne

![Velodyne](../img/velodyne/velodyne.png)

### Simulation Velodyne

A Velodyne lidar can be launched in simulation by creating a configuration with a *Lidar* of type *velodyne*.

### Hardware Velodyne

When using the Velodyne lidar, make sure that the IP-address of the host device (where the velodyne node is running) is set correctly in the settings. One can edit the settings of the velodyne using a web interface on it's IP-adress.

| ![Velodyne settings](../img/velodyne/velodyne_settings.png) | ![Teltonika settings](../img/teltonika/teltonika_settings.png) |
|-------------------------------------------------------------|----------------------------------------------------------------|

## Teltonika GPS

![Teltonika](../img/teltonika/nmea.png)

### Simulation Teltonika

A Teltonika GPS can be launched in simulation by creating a configuration with an *GPS* of type *teltonika*.

### Hardware Teltonika

When using the Teltonika GPS, make sure that the IP-address of the host device (where the nmea node is running) is set correctly in the settings. One can edit the settings of the Teltonika using a web interface on it’s IP-adress.
