# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0
#!/bin/bash
set -e

# Franka
git clone -b 2.1.0 https://github.com/frankarobotics/franka_description.git src/franka_description

# Husarion
git clone --depth=1 --filter=blob:none --sparse -b ros2 \
https://github.com/husarion/husarion_ugv_ros.git src/husarion_ugv_ros
cd src/husarion_ugv_ros
git sparse-checkout set husarion_ugv_description 
cd ../..

# Realsense
git clone --depth=1 --filter=blob:none --sparse -b 4.57.2 \
  https://github.com/IntelRealSense/realsense-ros.git src/realsense-ros
cd src/realsense-ros 
git sparse-checkout set realsense2_description
cd ../..

# Install dependencies
apt update && apt install -y --no-install-recommends \
  ros-$ROS_DISTRO-husarion-components-description \
  ros-$ROS_DISTRO-velodyne-description \
  ros-$ROS_DISTRO-zed-msgs
