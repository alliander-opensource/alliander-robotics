# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0
ARG BASE_IMAGE=ubuntu:latest
FROM $BASE_IMAGE 

ARG COLCON_BUILD_SEQUENTIAL
ENV ROS_DISTRO=jazzy
WORKDIR /rcdt/ros

# Install Docker CLI: 
RUN curl -fsSL https://get.docker.com | sh

# Install Doxygen:
RUN apt update && apt install -y --no-install-recommends \
    doxygen \
    && rm -rf /var/lib/apt/lists/* \
    && apt autoremove -y \
    && apt clean

# Install dependencies for ty:
RUN apt update && apt install -y --no-install-recommends \
    ros-$ROS_DISTRO-moveit-configs-utils \
    ros-$ROS_DISTRO-nav2-simple-commander \
    && rm -rf /var/lib/apt/lists/* \
    && apt autoremove -y \
    && apt clean

# Non-apt dependencies:
WORKDIR /rcdt/external
RUN git clone --depth=1 --filter=blob:none -b v3.1.1 \
    https://github.com/frankarobotics/franka_ros2.git src/franka_ros2 \
    && cd src/franka_ros2 \
    && git sparse-checkout set franka_msgs
RUN /rcdt/colcon_build.sh

# Install repo packages:
WORKDIR /rcdt/ros
COPY alliander_core/src/ /rcdt/ros/src
RUN /rcdt/colcon_build.sh

# Install python dependencies:
COPY pyproject.toml /rcdt/pyproject.toml
RUN uv sync --all-groups

WORKDIR /rcdt
ENTRYPOINT ["/entrypoint.sh"]
CMD ["sleep", "infinity"]
