# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0
FROM rcdt/robotics:base

ARG REMOTE_USER
ARG COLCON_BUILD_SEQUENTIAL
ENV ROS_DISTRO=jazzy
WORKDIR /rcdt/ros

# Install linting tools:
RUN apt update && apt install -y --no-install-recommends \
    doxygen \
    clang \
    && rm -rf /var/lib/apt/lists/* \
    && apt autoremove -y \
    && apt clean  

# Install MoveIt: 
RUN apt update && apt install -y --no-install-recommends \
    ros-$ROS_DISTRO-moveit \
    ros-$ROS_DISTRO-moveit-servo \
    ros-$ROS_DISTRO-moveit-visual-tools \
    ros-$ROS_DISTRO-moveit-ros-perception \
    ros-$ROS_DISTRO-topic-tools \
    && rm -rf /var/lib/apt/lists/* \
    && apt autoremove -y \
    && apt clean

# Install Nav2:
RUN apt update && apt install -y --no-install-recommends \
    ros-$ROS_DISTRO-nav2-simple-commander  \
    && rm -rf /var/lib/apt/lists/* \
    && apt autoremove -y \
    && apt clean

# Install custom msgs:
RUN git clone --depth=1 --filter=blob:none -b v3.1.1 \
  https://github.com/frankarobotics/franka_ros2.git src/franka_ros2 \
  && cd src/franka_ros2 \
  && git sparse-checkout set franka_msgs

# Setup configuration files:
COPY common/colcon_build.sh /rcdt/colcon_build.sh
COPY .devcontainer/dev/.dev_bashrc /.dev_bashrc
RUN echo "source /.dev_bashrc" >> /home/$REMOTE_USER/.bashrc

# Copy repo packages:
COPY rcdt_core/src/ /rcdt/ros/src
COPY rcdt_moveit/src/ /rcdt/ros/src

# Build repo packages:
ENV DCMAKE_EXPORT_COMPILE_COMMANDS=1
RUN /rcdt/colcon_build.sh

# Install python dependencies:
COPY pyproject.toml /rcdt/pyproject.toml
RUN uv sync --all-groups

WORKDIR /rcdt
CMD ["sleep", "infinity"]
