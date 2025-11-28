# syntax = devthefuture/dockerfile-x
# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0
ARG BASE_IMAGE=ubuntu:latest
FROM $BASE_IMAGE 

ARG COLCON_BUILD_SEQUENTIAL
ENV ROS_DISTRO=jazzy

# Install ROS dependencies 
RUN apt update && apt install -y --no-install-recommends \
    ros-$ROS_DISTRO-moveit \
    ros-$ROS_DISTRO-moveit-servo \
    ros-$ROS_DISTRO-moveit-visual-tools \
    ros-$ROS_DISTRO-ros2-controllers \
  && rm -rf /var/lib/apt/lists/* \
  && apt autoremove -y \
  && apt clean

# Franka ROS2 library
RUN apt update \
  && mkdir -p /rcdt/franka_ws/src \
  && cd /rcdt/franka_ws

RUN git clone -b v3.1.1 https://github.com/frankarobotics/franka_ros2.git src/franka_ros2 \
  && vcs import src --recursive --skip-existing <src/franka_ros2/franka.repos \
  && rosdep update --rosdistro $ROS_DISTRO \
  && rosdep install --from-paths src -y -i 

RUN . /opt/ros/$ROS_DISTRO/setup.sh \
  && colcon build --symlink-install --cmake-args -DCMAKE_BUILD_TYPE=Release \
  && echo "source /rcdt/franka_ws/install/setup.bash" >>/root/.bashrc

# Franka lock_unlock
RUN . /root/.bashrc \
  && apt update \
  && mkdir -p /rcdt/franka_lock_unlock/src \
  && cd /rcdt/franka_lock_unlock

RUN git clone https://github.com/alliander-opensource/franka_lock_unlock.git \
  && rosdep update --rosdistro $ROS_DISTRO \
  && rosdep install --from-paths src -y -i 

RUN . /opt/ros/$ROS_DISTRO/setup.sh \
  && colcon build --symlink-install --cmake-args -DCMAKE_BUILD_TYPE=Release \
  && echo "source /rcdt/franka_lock_unlock/install/setup.bash" >>/root/.bashrc

# Install dev packages
COPY dev-pkgs.txt /rcdt/dev-pkgs.txt
RUN apt update && apt install -y -qq --no-install-recommends  \
    `cat /rcdt/dev-pkgs.txt`\
    && rm -rf /var/lib/apt/lists/* \
    && apt autoremove \
    && apt clean

WORKDIR /rcdt
ENTRYPOINT ["/entrypoint.sh"]
CMD ["sleep", "infinity"]
