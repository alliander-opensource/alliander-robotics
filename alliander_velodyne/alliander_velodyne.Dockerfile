# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0
ARG BASE_IMAGE=ubuntu:latest
FROM $BASE_IMAGE 

ARG COLCON_BUILD_SEQUENTIAL
ENV ROS_DISTRO=jazzy

# Install ROS dependencies 
RUN apt update && apt install -y --no-install-recommends \
  ros-$ROS_DISTRO-velodyne-description \
  ros-$ROS_DISTRO-pointcloud-to-laserscan \
  && rm -rf /var/lib/apt/lists/* \
  && apt autoremove -y \
  && apt clean

# Install Velodyne packages:
WORKDIR /rcdt/external
RUN apt update \
  && git clone -b ros2 https://github.com/alliander-opensource/velodyne.git src/velodyne \
  && rosdep update --rosdistro $ROS_DISTRO \
  && rosdep install --from-paths src -y -i
RUN /rcdt/colcon_build.sh

# Install repo packages:
WORKDIR /rcdt/ros
COPY alliander_core/src/ /rcdt/ros/src
COPY alliander_velodyne/src/ /rcdt/ros/src
RUN /rcdt/colcon_build.sh

# Install python dependencies:
COPY pyproject.toml /rcdt/pyproject.toml
RUN uv sync

# Finalize
WORKDIR /rcdt
ENTRYPOINT ["/entrypoint.sh"]
CMD ["sleep", "infinity"]
