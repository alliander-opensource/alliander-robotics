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
  ros-$ROS_DISTRO-husarion-components-description \
  ros-$ROS_DISTRO-nmea-navsat-driver \
  ros-$ROS_DISTRO-robot-localization \
  && rm -rf /var/lib/apt/lists/* \
  && apt autoremove -y \
  && apt clean

# Install repo packages:
COPY rcdt_description/src/ /rcdt/ros/src
COPY rcdt_nmea/src/ /rcdt/ros/src
RUN . /opt/ros/$ROS_DISTRO/setup.sh \ 
  && colcon build --symlink-install --packages-up-to \
  rcdt_description \
  rcdt_nmea

# Finalize
WORKDIR /rcdt
ENTRYPOINT ["/entrypoint.sh"]
CMD ["sleep", "infinity"]
