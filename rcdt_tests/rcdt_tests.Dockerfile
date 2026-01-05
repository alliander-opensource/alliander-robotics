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

# Install repo packages:
COPY pyproject.toml /rcdt/pyproject.toml
COPY rcdt_core/src/ /rcdt/ros/src
COPY common/colcon_build.sh /rcdt/colcon_build.sh
RUN /rcdt/colcon_build.sh

WORKDIR /rcdt
ENTRYPOINT ["/entrypoint.sh"]
CMD ["sleep", "infinity"]
