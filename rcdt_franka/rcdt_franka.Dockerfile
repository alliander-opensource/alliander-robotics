# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0
ARG BASE_IMAGE=ubuntu:latest
FROM $BASE_IMAGE 

ARG COLCON_BUILD_SEQUENTIAL
ENV ROS_DISTRO=jazzy

# Install Franka packages:
WORKDIR /rcdt/external
RUN apt update \
  && git clone -b v3.1.1 https://github.com/frankarobotics/franka_ros2.git src/franka_ros2 \
  && vcs import src --recursive --skip-existing < src/franka_ros2/franka.repos \
  && rosdep update --rosdistro $ROS_DISTRO \
  && rosdep install --from-paths src -y -i
RUN /rcdt/colcon_build.sh

# Install repo packages:
WORKDIR /rcdt/ros
COPY rcdt_core/src/ /rcdt/ros/src
COPY rcdt_franka/src/ /rcdt/ros/src
RUN /rcdt/colcon_build.sh

# Install python dependencies:
COPY pyproject.toml /rcdt/pyproject.toml
RUN uv sync --group rcdt-franka

# Finalize
WORKDIR /rcdt
ENTRYPOINT ["/entrypoint.sh"]
CMD ["sleep", "infinity"]
