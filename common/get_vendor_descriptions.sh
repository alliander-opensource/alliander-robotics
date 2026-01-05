# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0
#!/bin/bash
set -e

# Franka
cd /rcdt/ros/src
git clone -b jazzy https://github.com/frankarobotics/franka_description.git

# Husarion
git clone --depth=1 --filter=blob:none --sparse -b ros2 \
  https://github.com/husarion/husarion_ugv_ros.git
cd husarion_ugv_ros
git sparse-checkout set husarion_ugv_description 
cd /rcdt/ros/src

# Realsense
git clone --depth=1 --filter=blob:none --sparse -b 4.57.2 \
  https://github.com/IntelRealSense/realsense-ros.git
cd realsense-ros 
git sparse-checkout set realsense2_description
cd /rcdt/ros/src

# Install dependencies
apt update && apt install -y --no-install-recommends \
  ros-$ROS_DISTRO-husarion-components-description \
  ros-$ROS_DISTRO-velodyne-description \
  ros-$ROS_DISTRO-zed-msgs
