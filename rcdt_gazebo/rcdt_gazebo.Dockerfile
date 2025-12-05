# syntax = devthefuture/dockerfile-x
# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0
ARG BASE_IMAGE=ubuntu:latest
FROM $BASE_IMAGE 

ARG COLCON_BUILD_SEQUENTIAL
ENV ROS_DISTRO=jazzy

# Add custom packages
WORKDIR /rcdt/ros
COPY rcdt_gazebo/src/ /rcdt/ros/src
COPY pyproject.toml /rcdt/pyproject.toml

# Install ROS dependencies 
RUN apt update && apt install -y --no-install-recommends \
  unzip \
  ros-$ROS_DISTRO-ros-gz \
  ros-$ROS_DISTRO-gz-ros2-control \
  && rm -rf /var/lib/apt/lists/* \
  && apt autoremove -y \
  && apt clean

# Install osm2world
RUN mkdir -p /rcdt/osm2world \
  && cd /rcdt/osm2world \
  && wget https://osm2world.org/download/files/latest/OSM2World-latest-bin.zip \
  && unzip OSM2World-latest-bin.zip \
  && rm OSM2World-latest-bin.zip

# Get all necessary models
WORKDIR /rcdt/ros/src
RUN git clone -b jazzy https://github.com/frankarobotics/franka_description.git \
  && git clone -b ros2 https://github.com/husarion/husarion_ugv_ros.git \
  && cd /rcdt/ros \
  && . /opt/ros/$ROS_DISTRO/setup.sh \ 
  && colcon build --symlink-install --packages-up-to \
  franka_description \
  husarion_ugv_description \
  rcdt_gazebo
 
# Install dev packages
COPY common/dev-pkgs.txt /rcdt/dev-pkgs.txt
RUN apt update && apt install -y -qq --no-install-recommends  \
    `cat /rcdt/dev-pkgs.txt`\
    && rm -rf /var/lib/apt/lists/* \
    && apt autoremove \
    && apt clean

WORKDIR /rcdt
ENTRYPOINT ["/entrypoint.sh"]
CMD ["sleep", "infinity"]
