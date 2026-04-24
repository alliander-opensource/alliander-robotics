# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0
ARG BASE_IMAGE=ubuntu:latest
FROM $BASE_IMAGE 

ARG COLCON_BUILD_SEQUENTIAL
ENV ROS_DISTRO=jazzy

# Install Ewellix packages:
WORKDIR /$WORKDIR/external
RUN apt update \
  && apt install -y ros-$ROS_DISTRO-ewellix-description \
  && git clone -b 0.2.3 https://github.com/clearpathrobotics/ewellix_lift.git src/ewellix_lift \
  && git clone https://github.com/joshnewans/serial.git src/serial \
  && rosdep update --rosdistro $ROS_DISTRO \
  && rosdep install --from-paths src -y -i
RUN /$WORKDIR/colcon_build.sh

# Install repo packages:
WORKDIR /$WORKDIR/ros
COPY alliander_core/src/ /$WORKDIR/ros/src
COPY alliander_ewellix/src/ /$WORKDIR/ros/src
RUN /$WORKDIR/colcon_build.sh

# Install python dependencies:
WORKDIR $WORKDIR
COPY pyproject.toml/ /$WORKDIR/pyproject.toml
RUN uv sync --group alliander-gps \
  && echo "export PYTHONPATH=\"$(dirname $(dirname $(uv python find)))/lib/python3.12/site-packages:\$PYTHONPATH\"" >> /root/.bashrc \
  && echo "export PATH=\"$(dirname $(dirname $(uv python find)))/bin:\$PATH\"" >> /root/.bashrc

# Finalize
WORKDIR /$WORKDIR
ENTRYPOINT ["/entrypoint.sh"]
CMD ["sleep", "infinity"]
