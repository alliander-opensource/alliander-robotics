<!--
SPDX-FileCopyrightText: Alliander N. V.

SPDX-License-Identifier: Apache-2.0
-->

# Input Devices

This page describes the use of the different input devices we support.

## Joystick

Arm and Vehicle platforms can be controlled using a joystick. To do this, connect a joystick to the USB interface of the host device that will run the Alliander Robotics software stack. To activate joystick control, pass the `--joystick` or `-j` flag to the `uv run start.py` command when launching a configuration.

## Meta Quest 3

Arm platforms can be controlled using a Meta Quest 3. To do this, we make use of the [meta_quest_teleop](https://github.com/NeuracoreAI/meta_quest_teleop) tool. Make sure to install the APK on the Quest and enable USB debugging if not done already.

### Install ADB

The tool requires Android Debug Bridge (ADB) to work. Make sure to install ADB on the host device that will run the Alliander Robotics software stack:

```bash
sudo apt install android-tools-adb
```

Next, connect the Quest to the host device via USB. You should see the Quest as:

```bash
ID XXXX:YYYY Oculus VR, Inc. Quest 3
```

Where `XXXX` and `YYYY` are four numbers. Next, create an udev rule for the Quest, by adding the following line to `/etc/udev/rules.d/51-android.rules`:

```bash
SUBSYSTEM=="usb", ATTR{idVendor}=="XXXX", ATTR{idProduct}=="YYYY", MODE="0666", GROUP="plugdev"
```

Make sure to replace `XXXX` and `YYYY` with the correct numbers. Now, run `adb devices` and select `Always allow from this computer` on the Quest. You should see the following response:

```bash
List of devices attached
<SERIAL_NUMBER> device

```

### Control an Arm platform using the Quest

**Run ADB on host device**
\
Make sure that the ADB deamon is already running on the host device, by checking for the expected response on the `adb devices command`. If the ADB deamon is not running on the host device, the docker container will launch an ADB deamon. The Quest sees this as a different computer, asking again for USB debugging alowence, failing the Docker container to start.

**Run the app and keep Quest on**
\
Next, start the meta_quest_teleop app if not already running. Note that by default, the Quest turns off when you do are not wearing it. To avoid this, you can turn off the proximity sensor using:

```bash
adb shell am broadcast -a com.oculus.vrpowermanager.prox_close
```

You can enable the proximity sensor again using:

```bash
shell am broadcast -a com.oculus.vrpowermanager.automation_disable
```

**Start the software stack**
\
To activate Meta Quest control, pass the `--meta` or `-m` flag to the `uv run start.py` command when launching a configuration. When an Arm platform with MoveIt Servo is started, you should be able to switch MoveIt Servo to pose tracking by pressing the Grip button on the side of the right Controller.

Make sure that the Controller is always in view of the Quest Headset and place the Headset statically in the room. The app measures the Controller position relative to the Quest Headset, so movement of the Headset results in Controller movements for the system.

Finally, when you hold the Trigger on the right Controller, the arm should copy the movements made with the Controller. To Home the arm, press the A button.

:::{video} ../vid/input_devices/quest_control.mp4
:width: 100%
:::