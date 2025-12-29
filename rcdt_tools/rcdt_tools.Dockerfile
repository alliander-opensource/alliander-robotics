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
RUN apt update \
  && cd /rcdt/ros/src \
  && git clone -b ros2 https://github.com/MoffKalast/vizanti.git \
  && git clone -b jazzy https://github.com/alliander-opensource/rws.git \
  && cd /rcdt/ros \
  && rosdep update --rosdistro $ROS_DISTRO \
  && rosdep install --from-paths src -y -i

# Install vendor descriptions:
WORKDIR /rcdt/ros/src
RUN apt update && apt install -y --no-install-recommends \
  ros-$ROS_DISTRO-husarion-components-description \
  ros-$ROS_DISTRO-velodyne-description \
  ros-$ROS_DISTRO-zed-msgs \
  && git clone -b 4.57.2 https://github.com/IntelRealSense/realsense-ros.git \
  && git clone -b jazzy https://github.com/frankarobotics/franka_description.git \
  && git clone -b ros2 https://github.com/husarion/husarion_ugv_ros.git \
  && cd /rcdt/ros \
  && . /opt/ros/$ROS_DISTRO/setup.sh \ 
  && colcon build --symlink-install --packages-up-to \
  franka_description \
  husarion_ugv_description \
  realsense2_description

# Install repo packages:
COPY rcdt_description/src/ /rcdt/ros/src
COPY rcdt_tools/src/ /rcdt/ros/src
RUN cd /rcdt/ros \
  && . /opt/ros/$ROS_DISTRO/setup.sh \ 
  && colcon build --symlink-install --packages-up-to \
  rcdt_description \
  rcdt_tools

WORKDIR /rcdt
ENTRYPOINT ["/entrypoint.sh"]
CMD ["sleep", "infinity"]
