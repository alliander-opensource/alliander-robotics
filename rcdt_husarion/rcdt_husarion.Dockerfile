# syntax = devthefuture/dockerfile-x
# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0
ARG BASE_IMAGE=ubuntu:latest
FROM $BASE_IMAGE 

ARG COLCON_BUILD_SEQUENTIAL
ENV ROS_DISTRO=jazzy

# Install ROS dependencies 
RUN apt update && apt install -y --no-install-recommends \
    ros-$ROS_DISTRO-navigation2 \
    ros-$ROS_DISTRO-nav2-bringup \
    ros-$ROS_DISTRO-slam-toolbox \
  && rm -rf /var/lib/apt/lists/* \
  && apt autoremove -y \
  && apt clean

# Add custom packages
WORKDIR /rcdt/ros
COPY rcdt_husarion/src/ /rcdt/ros/src
COPY pyproject.toml /rcdt/pyproject.toml

# Add nav2 packages 
RUN mkdir -p /rcdt/ros/src \
  && cd /rcdt/ros/src \
  && git clone -b jazzy-devel https://github.com/blackcoffeerobotics/vector_pursuit_controller.git \
  && cd /rcdt/ros

# Add Husarion packages
RUN apt update \
  && mkdir -p /rcdt/ros/src \
  && cd /rcdt/ros \
  && git clone -b 2.3.1 https://github.com/husarion/husarion_ugv_ros.git src/husarion_ugv_ros \
  && export HUSARION_ROS_BUILD_TYPE=simulation \ 
  && vcs import src < src/husarion_ugv_ros/husarion_ugv/${HUSARION_ROS_BUILD_TYPE}_deps.repos \
  && rosdep update --rosdistro $ROS_DISTRO \
  && rosdep install --from-paths src -y -i

RUN uv sync \
  && . /opt/ros/$ROS_DISTRO/setup.sh \ 
  && colcon build --symlink-install \
  --packages-up-to vector_pursuit_controller husarion_ugv husarion_ugv_description rcdt_husarion \
  --cmake-args -DCMAKE_BUILD_TYPE=Release \ 
  --event-handlers console_direct+

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
