# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0
ARG BASE_IMAGE=ubuntu:latest
FROM $BASE_IMAGE 

ARG COLCON_BUILD_SEQUENTIAL
ENV ROS_DISTRO=jazzy

# Install ROS dependencies 
RUN apt update && apt install -y --no-install-recommends \
  ros-$ROS_DISTRO-moveit \
  ros-$ROS_DISTRO-moveit-servo \
  ros-$ROS_DISTRO-moveit-visual-tools \
  ros-$ROS_DISTRO-moveit-ros-perception \
  ros-$ROS_DISTRO-topic-tools \
  && rm -rf /var/lib/apt/lists/* \
  && apt autoremove -y \
  && apt clean

# Get required descriptions:
WORKDIR /rcdt/ros/src
RUN git clone -b jazzy https://github.com/frankarobotics/franka_description.git 

# Install repo packages
COPY pyproject.toml /rcdt/pyproject.toml
COPY rcdt_core/src/ /rcdt/ros/src
COPY rcdt_moveit/src/ /rcdt/ros/src
COPY common/colcon_build.sh /rcdt/colcon_build.sh
RUN /rcdt/colcon_build.sh

# Finalize
WORKDIR /rcdt
ENTRYPOINT ["/entrypoint.sh"]
CMD ["sleep", "infinity"]
