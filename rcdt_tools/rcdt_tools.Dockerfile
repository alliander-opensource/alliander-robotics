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
COPY rcdt_tools/src/ /rcdt/ros/src
COPY pyproject.toml /rcdt/pyproject.toml

# Install ROS dependencies 
RUN apt update && apt install -y --no-install-recommends \
    ros-dev-tools \
    ros-$ROS_DISTRO-launch-pytest \
    ros-$ROS_DISTRO-plotjuggler-ros \
    ros-$ROS_DISTRO-rmw-cyclonedds-cpp \
    ros-$ROS_DISTRO-rqt-tf-tree \
    ros-$ROS_DISTRO-rviz-satellite \
    ros-$ROS_DISTRO-vision-msgs \
  && rm -rf /var/lib/apt/lists/* \
  && apt autoremove -y \
  && apt clean

# Get vizanti and install its dependencies
RUN apt update \
  && cd /rcdt/ros/src \
  && git clone -b ros2 https://github.com/MoffKalast/vizanti.git \
  && git clone -b jazzy https://github.com/alliander-opensource/rws.git \
  && cd /rcdt/ros \
  && rosdep update --rosdistro $ROS_DISTRO \
  && rosdep install --from-paths src -y -i

RUN cd /rcdt/ros \
  && uv sync \
  && . /opt/ros/$ROS_DISTRO/setup.sh \ 
  && colcon build --symlink-install \
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
