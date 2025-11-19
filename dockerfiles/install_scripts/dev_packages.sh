#!/bin/bash -i

# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

set -e
source /home/$UNAME/.bashrc
apt update

apt install -y \
    clang \
    doxygen \
    xvfb \
    ros-$ROS_DISTRO-nmea-navsat-driver \
    ros-$ROS_DISTRO-moveit-ros-perception \
    ros-$ROS_DISTRO-topic-tools \
    ros-$ROS_DISTRO-rviz-satellite
