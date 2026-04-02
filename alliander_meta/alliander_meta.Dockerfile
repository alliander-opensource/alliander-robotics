# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0
ARG BASE_IMAGE=ubuntu:latest
FROM $BASE_IMAGE 

ARG COLCON_BUILD_SEQUENTIAL
ENV ROS_DISTRO=jazzy

# Install Meta packages:
WORKDIR /$WORKDIR/external
RUN apt update
RUN echo "Clone and install" \
  && git clone -b main-ros2 https://github.com/leggedrobotics/ROS-TCP-Endpoint.git src/ROS-TCP-Endpoint \
  && git clone -b main-ros2 https://github.com/leggedrobotics/vr_haptic_msgs.git src/vr_haptic_msgs \
  && git clone https://github.com/NVIDIA-ISAAC-ROS/isaac_ros_nvblox.git /isaac_ros_nvblox \
  && mv /isaac_ros_nvblox/nvblox_msgs src/
RUN /$WORKDIR/colcon_build.sh

# Install repo packages:
WORKDIR /$WORKDIR/ros
COPY alliander_core/src/ /$WORKDIR/ros/src
COPY alliander_meta/src/ /$WORKDIR/ros/src
RUN /$WORKDIR/colcon_build.sh

# Install python dependencies:
WORKDIR $WORKDIR
COPY pyproject.toml/ /$WORKDIR/pyproject.toml
RUN uv sync --group alliander-meta \
  && echo "export PYTHONPATH=\"$(dirname $(dirname $(uv python find)))/lib/python3.12/site-packages:\$PYTHONPATH\"" >> /root/.bashrc \
  && echo "export PATH=\"$(dirname $(dirname $(uv python find)))/bin:\$PATH\"" >> /root/.bashrc

# Finalize
WORKDIR /$WORKDIR
ENTRYPOINT ["/entrypoint.sh"]
CMD ["sleep", "infinity"]
