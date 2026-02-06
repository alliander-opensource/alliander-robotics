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

# Install nav2 packages 
WORKDIR /rcdt/external
RUN git clone -b jazzy-devel https://github.com/blackcoffeerobotics/vector_pursuit_controller.git src/vector_pursuit_controller
RUN /rcdt/colcon_build.sh

# Install repo packages:
WORKDIR /rcdt/ros
COPY alliander_core/src/ /rcdt/ros/src
COPY alliander_nav2/src/ /rcdt/ros/src
RUN /rcdt/colcon_build.sh

# Install python dependencies:
COPY pyproject.toml /rcdt/pyproject.toml
RUN uv sync --group alliander-nav2

WORKDIR /rcdt
ENTRYPOINT ["/entrypoint.sh"]
CMD ["sleep", "infinity"]
