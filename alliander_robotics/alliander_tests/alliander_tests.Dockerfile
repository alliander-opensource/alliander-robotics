# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0
ARG BASE_IMAGE=ubuntu:latest
FROM $BASE_IMAGE 

ARG COLCON_BUILD_SEQUENTIAL
ENV ROS_DISTRO=jazzy

# Install Docker CLI: 
RUN curl -fsSL https://get.docker.com | sh

# Install Doxygen:
RUN apt update && apt install -y --no-install-recommends \
    doxygen \
    && rm -rf /var/lib/apt/lists/* \
    && apt autoremove -y \
    && apt clean

# Install dependencies for ty:
RUN apt update && apt install -y --no-install-recommends \
    ros-$ROS_DISTRO-moveit-configs-utils \
    ros-$ROS_DISTRO-nav2-simple-commander \
    && rm -rf /var/lib/apt/lists/* \
    && apt autoremove -y \
    && apt clean

# Non-apt dependencies:
WORKDIR /$WORKDIR/external
RUN git clone --depth=1 --filter=blob:none -b v3.1.1 \
    https://github.com/frankarobotics/franka_ros2.git src/franka_ros2 \
    && cd src/franka_ros2 \
    && git sparse-checkout set franka_msgs
RUN /$WORKDIR/colcon_build.sh

# Install repo packages:
WORKDIR /$WORKDIR/ros
COPY alliander_robotics/alliander_core/src/ /$WORKDIR/ros/src
RUN /$WORKDIR/colcon_build.sh

# Install python dependencies:
WORKDIR $WORKDIR
COPY pyproject.toml /$WORKDIR/pyproject.toml
RUN uv sync --all-groups \
    && echo "export PYTHONPATH=\"$(dirname $(dirname $(uv python find)))/lib/python3.12/site-packages:\$PYTHONPATH\"" >> /root/.bashrc \
    && echo "export PATH=\"$(dirname $(dirname $(uv python find)))/bin:\$PATH\"" >> /root/.bashrc

WORKDIR /$WORKDIR
ENTRYPOINT ["/entrypoint.sh"]
CMD ["sleep", "infinity"]
