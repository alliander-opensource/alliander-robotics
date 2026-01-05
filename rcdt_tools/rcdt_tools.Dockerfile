# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0
ARG BASE_IMAGE=ubuntu:latest
FROM $BASE_IMAGE 

ARG COLCON_BUILD_SEQUENTIAL
ENV ROS_DISTRO=jazzy

# Install ROS dependencies 
RUN apt update && apt install -y --no-install-recommends \
  ros-dev-tools \
  ros-$ROS_DISTRO-launch-pytest \
  ros-$ROS_DISTRO-plotjuggler-ros \
  ros-$ROS_DISTRO-rmw-cyclonedds-cpp \
  ros-$ROS_DISTRO-rqt-tf-tree \
  ros-$ROS_DISTRO-moveit-ros-visualization \
  ros-$ROS_DISTRO-rviz-satellite \
  ros-$ROS_DISTRO-vision-msgs \
  && rm -rf /var/lib/apt/lists/* \
  && apt autoremove -y \
  && apt clean

# Get vizanti and install its dependencies
WORKDIR /rcdt/ros
RUN apt update \
  && git clone -b ros2 https://github.com/MoffKalast/vizanti.git src/vizanti \
  && git clone -b jazzy https://github.com/alliander-opensource/rws.git src/rws \
  && rosdep update --rosdistro $ROS_DISTRO \
  && rosdep install --from-paths src -y -i

# Install vendor descriptions:
COPY common/get_vendor_descriptions.sh /rcdt/get_vendor_descriptions.sh
RUN /rcdt/get_vendor_descriptions.sh && rm /rcdt/get_vendor_descriptions.sh

# Install repo packages:
COPY pyproject.toml /rcdt/pyproject.toml
COPY rcdt_core/src/ /rcdt/ros/src
COPY rcdt_tools/src/ /rcdt/ros/src
COPY common/colcon_build.sh /rcdt/colcon_build.sh
RUN /rcdt/colcon_build.sh

# Finalize
WORKDIR /rcdt
ENTRYPOINT ["/entrypoint.sh"]
CMD ["sleep", "infinity"]
