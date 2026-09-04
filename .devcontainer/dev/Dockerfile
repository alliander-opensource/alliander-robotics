# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0
FROM allianderrobotics/base

ARG REMOTE_USER
ARG SRC_DIRECTORY=alliander_robotics
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
    ros-$ROS_DISTRO-imu-filter-madgwick \
    ros-$ROS_DISTRO-moveit \
    ros-$ROS_DISTRO-moveit-servo \
    ros-$ROS_DISTRO-moveit-visual-tools \
    ros-$ROS_DISTRO-moveit-ros-perception \
    ros-$ROS_DISTRO-topic-tools \
    ros-$ROS_DISTRO-navigation2 \
    ros-$ROS_DISTRO-nav2-bringup \
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
RUN apt update && apt install -y --no-install-recommends \
    ros-$ROS_DISTRO-ewellix-interfaces \
    && rm -rf /var/lib/apt/lists/* \
    && apt autoremove -y \
    && apt clean
RUN git clone --depth=1 --filter=blob:none -b v3.1.1 \
    https://github.com/frankarobotics/franka_ros2.git src/franka_ros2 \
    && cd src/franka_ros2 \
    && git sparse-checkout set franka_msgs
RUN git clone --depth=1 --filter=blob:none -b v4.6-0 \
    https://github.com/NVIDIA-ISAAC-ROS/isaac_ros_common.git src/isaac_ros_common \
    && cd src/isaac_ros_common \
    && git sparse-checkout set isaac_ros_apriltag_interfaces \
    && sed -i '25d' isaac_ros_apriltag_interfaces/package.xml \
    && sed -i '48,51d' isaac_ros_apriltag_interfaces/CMakeLists.txt

# Install debug tools:
RUN apt update && apt install -y --no-install-recommends \
    ros-$ROS_DISTRO-plotjuggler-ros \
    ros-$ROS_DISTRO-rqt-tf-tree

# Setup configuration files:
COPY .devcontainer/dev/.dev_bashrc /.dev_bashrc
RUN echo "source /.dev_bashrc" >> /home/$REMOTE_USER/.bashrc

# Copy Alliander ROS packages with C++ code, install build dependencies and build the packages:
COPY $SRC_DIRECTORY/alliander_isaac/src /alliander/ros/src
COPY $SRC_DIRECTORY/alliander_core/src/ /alliander/ros/src
COPY $SRC_DIRECTORY/alliander_diagnostics/src/ /alliander/ros/src
COPY $SRC_DIRECTORY/alliander_franka/src/ /alliander/ros/src
COPY $SRC_DIRECTORY/alliander_joystick/src/ /alliander/ros/src
COPY $SRC_DIRECTORY/alliander_meta/src/ /alliander/ros/src
COPY $SRC_DIRECTORY/alliander_moveit/src/ /alliander/ros/src
COPY $SRC_DIRECTORY/alliander_nav2/src/ /alliander/ros/src
COPY $SRC_DIRECTORY/alliander_robotiq/src /alliander/ros/src
COPY $SRC_DIRECTORY/alliander_seekthermal/src/ /alliander/ros/src
COPY $SRC_DIRECTORY/alliander_xsens/src/ /alliander/ros/src
COPY $SRC_DIRECTORY/utilities/ /alliander/ros/src
RUN /alliander/rosdep_install.sh --build
RUN /alliander/colcon_build.sh

# Install python dependencies:
COPY $SRC_DIRECTORY/pyproject.toml /alliander/pyproject.toml
RUN --mount=type=cache,id=uv-cache,target=/root/.cache/uv uv sync --all-groups

WORKDIR /alliander
CMD ["sleep", "infinity"]
