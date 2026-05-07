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
RUN mkdir -p /$WORKDIR/osm2world \
  && cd /$WORKDIR/osm2world \
  && wget https://osm2world.org/download/files/latest/OSM2World-latest-bin.zip \
  && unzip OSM2World-latest-bin.zip \
  && rm OSM2World-latest-bin.zip

# Install vendor descriptions:
WORKDIR /$WORKDIR/external
COPY common/get_vendor_descriptions.sh /$WORKDIR/get_vendor_descriptions.sh
RUN /$WORKDIR/get_vendor_descriptions.sh && rm /$WORKDIR/get_vendor_descriptions.sh
RUN /$WORKDIR/colcon_build.sh

# Install repo packages:
WORKDIR /$WORKDIR/ros
COPY alliander_robotics/alliander_core/src/ /$WORKDIR/ros/src
COPY alliander_robotics/alliander_gazebo/src/ /$WORKDIR/ros/src
RUN /$WORKDIR/colcon_build.sh

# Install python dependencies:
WORKDIR $WORKDIR
COPY pyproject.toml /$WORKDIR/pyproject.toml
RUN uv sync --group alliander-gazebo  \
  && echo "export PYTHONPATH=\"$(dirname $(dirname $(uv python find)))/lib/python3.12/site-packages:\$PYTHONPATH\"" >> /root/.bashrc \
  && echo "export PATH=\"$(dirname $(dirname $(uv python find)))/bin:\$PATH\"" >> /root/.bashrc

WORKDIR /$WORKDIR
ENTRYPOINT ["/entrypoint.sh"]
CMD ["sleep", "infinity"]
