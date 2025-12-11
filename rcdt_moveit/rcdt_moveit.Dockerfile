# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0
ARG BASE_IMAGE=ubuntu:latest
FROM $BASE_IMAGE 

ARG COLCON_BUILD_SEQUENTIAL
ENV ROS_DISTRO=jazzy
WORKDIR /rcdt/ros
COPY pyproject.toml /rcdt/pyproject.toml

# Install ROS dependencies 
RUN apt update && apt install -y --no-install-recommends \
    ros-$ROS_DISTRO-moveit \
    ros-$ROS_DISTRO-moveit-servo \
    ros-$ROS_DISTRO-moveit-visual-tools \
  && rm -rf /var/lib/apt/lists/* \
  && apt autoremove -y \
  && apt clean

# Get required descriptions:
WORKDIR /rcdt/ros/src
RUN git clone -b jazzy https://github.com/frankarobotics/franka_description.git

# Install dev packages
COPY common/dev-pkgs.txt /rcdt/dev-pkgs.txt
RUN apt update && apt install -y -qq --no-install-recommends  \
    `cat /rcdt/dev-pkgs.txt`\
    && rm -rf /var/lib/apt/lists/* \
    && apt autoremove \
    && apt clean

# Install repo packages
WORKDIR /rcdt/ros
COPY rcdt_moveit/src/ /rcdt/ros/src
RUN uv sync \
  && . /opt/ros/$ROS_DISTRO/setup.sh \ 
  && colcon build --symlink-install \
  --cmake-args -DCMAKE_BUILD_TYPE=Release \ 
  --cmake-args=-DCMAKE_EXPORT_COMPILE_COMMANDS:BOOL=ON \
  --event-handlers console_direct+

# Finalize
WORKDIR /rcdt
ENTRYPOINT ["/entrypoint.sh"]
CMD ["sleep", "infinity"]
