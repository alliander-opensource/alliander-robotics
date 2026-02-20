# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0
FROM allianderrobotics/base

ARG REMOTE_USER
ARG COLCON_BUILD_SEQUENTIAL
ENV ROS_DISTRO=jazzy
WORKDIR /alliander/ros

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
COPY .devcontainer/dev/.dev_bashrc /.dev_bashrc
RUN echo "source /.dev_bashrc" >> /home/$REMOTE_USER/.bashrc

# Copy repo packages:
COPY alliander_core/src/ /alliander/ros/src
COPY alliander_franka/src/ /alliander/ros/src
COPY alliander_joystick/src/ /alliander/ros/src
COPY alliander_moveit/src/ /alliander/ros/src

# Build repo packages:
RUN /alliander/colcon_build.sh

# Install python dependencies:
COPY pyproject.toml /alliander/pyproject.toml
RUN uv sync --all-groups

WORKDIR /alliander
CMD ["sleep", "infinity"]
