# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0
ARG BASE_IMAGE=ubuntu:latest
FROM $BASE_IMAGE 

ARG COLCON_BUILD_SEQUENTIAL
ENV ROS_DISTRO=jazzy
WORKDIR /rcdt/ros
COPY pyproject.toml /rcdt/pyproject.toml

# Install Franka packages:
RUN apt update \
  && mkdir -p /rcdt/ros/src \
  && cd /rcdt/ros \
  && git clone -b v3.1.1 https://github.com/frankarobotics/franka_ros2.git src/franka_ros2 \
  && vcs import src --recursive --skip-existing <src/franka_ros2/franka.repos \
  && rosdep update --rosdistro $ROS_DISTRO \
  && rosdep install --from-paths src -y -i

RUN uv sync \
  && . /opt/ros/$ROS_DISTRO/setup.sh \ 
  && colcon build --symlink-install \
  --cmake-args -DCMAKE_BUILD_TYPE=Release \ 
  --event-handlers console_direct+

# Install dev packages
COPY common/dev-pkgs.txt /rcdt/dev-pkgs.txt
RUN apt update && apt install -y -qq --no-install-recommends  \
  `cat /rcdt/dev-pkgs.txt`\
  && rm -rf /var/lib/apt/lists/* \
  && apt autoremove \
  && apt clean

# Install repo packages:
COPY rcdt_description/src/ /rcdt/ros/src
COPY rcdt_franka/src/ /rcdt/ros/src
RUN . /opt/ros/$ROS_DISTRO/setup.sh \ 
  && colcon build --symlink-install --packages-up-to \
  rcdt_description \
  rcdt_franka

# Finalize
WORKDIR /rcdt
ENTRYPOINT ["/entrypoint.sh"]
CMD ["sleep", "infinity"]
