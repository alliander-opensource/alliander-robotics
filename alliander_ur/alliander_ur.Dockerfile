# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0
ARG BASE_IMAGE=ubuntu:latest
FROM $BASE_IMAGE 

ARG COLCON_BUILD_SEQUENTIAL
ENV ROS_DISTRO=jazzy

# Install UR packages
# WORKDIR /$WORKDIR/external
# RUN apt update \
#   && git clone -b 4.5.0 https://github.com/UniversalRobots/Universal_Robots_ROS2_Driver.git src/Universal_Robots_ROS2_Driver \
#   && vcs import src --recursive --skip-existing < src/Universal_Robots_ROS2_Driver/Universal_Robots_ROS2_Driver.${ROS_DISTRO}.repos \
#   && rosdep update --rosdistro $ROS_DISTRO \
#   && rosdep install --from-paths src -y -i
# RUN /$WORKDIR/colcon_build.sh
RUN apt update && apt install -y --no-install-recommends \
  ros-$ROS_DISTRO-ur \
  ros-$ROS_DISTRO-ur-simulation-gz \
  ros-$ROS_DISTRO-ur-description \
  ros-$ROS_DISTRO-ur-moveit-config \
  ros-$ROS_DISTRO-ur-robot-driver \
  && rm -rf /var/lib/apt/lists/* \
  && apt autoremove -y \
  && apt clean

# Install repo packages:
WORKDIR /$WORKDIR/ros
COPY alliander_core/src/ /$WORKDIR/ros/src
COPY alliander_ur/src/ /$WORKDIR/ros/src
RUN /$WORKDIR/colcon_build.sh

# Install python dependencies:
WORKDIR $WORKDIR
COPY pyproject.toml /$WORKDIR/pyproject.toml
RUN uv sync  \
  && echo "export PYTHONPATH=\"$(dirname $(dirname $(uv python find)))/lib/python3.12/site-packages:\$PYTHONPATH\"" >> /root/.bashrc \
  && echo "export PATH=\"$(dirname $(dirname $(uv python find)))/bin:\$PATH\"" >> /root/.bashrc

WORKDIR /$WORKDIR
ENTRYPOINT ["/entrypoint.sh"]
CMD ["sleep", "infinity"]
