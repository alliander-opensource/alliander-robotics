# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0
ARG BASE_IMAGE=ubuntu:latest
FROM $BASE_IMAGE 

ARG COLCON_BUILD_SEQUENTIAL
ENV ROS_DISTRO=jazzy

# Install ROS dependencies 
RUN apt update && apt install -y --no-install-recommends \
  unzip \
  ros-$ROS_DISTRO-ros-gz \
  ros-$ROS_DISTRO-gz-ros2-control \
  ros-$ROS_DISTRO-ros2-controllers \
  && rm -rf /var/lib/apt/lists/* \
  && apt autoremove -y \
  && apt clean

# Install osm2world
RUN mkdir -p /rcdt/osm2world \
  && cd /rcdt/osm2world \
  && wget https://osm2world.org/download/files/latest/OSM2World-latest-bin.zip \
  && unzip OSM2World-latest-bin.zip \
  && rm OSM2World-latest-bin.zip

# Install vendor descriptions:
WORKDIR /rcdt/external
COPY common/get_vendor_descriptions.sh /rcdt/get_vendor_descriptions.sh
RUN /rcdt/get_vendor_descriptions.sh && rm /rcdt/get_vendor_descriptions.sh
RUN /rcdt/colcon_build.sh

# Install repo packages:
WORKDIR /rcdt/ros
COPY rcdt_core/src/ /rcdt/ros/src
COPY rcdt_gazebo/src/ /rcdt/ros/src
RUN /rcdt/colcon_build.sh

# Install python dependencies:
COPY pyproject.toml /rcdt/pyproject.toml
RUN uv sync --group rcdt-gazebo

WORKDIR /rcdt
ENTRYPOINT ["/entrypoint.sh"]
CMD ["sleep", "infinity"]
