# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0
ARG BASE_IMAGE=ubuntu:latest
FROM $BASE_IMAGE AS builder

##############################
# Build stage
##############################

ARG SRC_DIRECTORY
ARG COLCON_BUILD_SEQUENTIAL
ENV ROS_DISTRO=jazzy

# Copy Alliander ROS packages, install build dependencies and build the packages:
WORKDIR /$WORKDIR/ros
COPY $SRC_DIRECTORY/alliander_core/src/ /$WORKDIR/ros/src
COPY $SRC_DIRECTORY/alliander_robotiq/src/ /$WORKDIR/ros/src
COPY $SRC_DIRECTORY/descriptions/alliander_robotiq_description/ /$WORKDIR/ros/src/alliander_robotiq_description/
RUN apt update && rosdep update --rosdistro $ROS_DISTRO && rosdep install --from-paths /$WORKDIR/ros/src -y -i -t build
RUN /$WORKDIR/colcon_build.sh

# Install python dependencies:
WORKDIR $WORKDIR
COPY $SRC_DIRECTORY/pyproject.toml /$WORKDIR/pyproject.toml
RUN uv sync --group alliander-robotiq  \
  && echo "export PYTHONPATH=\"$(dirname $(dirname $(uv python find)))/lib/python3.12/site-packages:\$PYTHONPATH\"" >> /root/.bashrc \
  && echo "export PATH=\"$(dirname $(dirname $(uv python find)))/bin:\$PATH\"" >> /root/.bashrc

##############################
# Runtime stage
##############################

FROM ${BASE_IMAGE}
ENV ROS_DISTRO=jazzy

# Copy Alliander ROS packages and install runtime dependencies:
COPY --from=builder /$WORKDIR/ros /$WORKDIR/ros
RUN apt update && rosdep update --rosdistro $ROS_DISTRO && rosdep install --from-paths /$WORKDIR/ros/src -y -i -t exec

# Copy environments
COPY --from=builder /$WORKDIR/.venv /$WORKDIR/.venv
COPY --from=builder /root/.bashrc /root/.bashrc

# Finalize
WORKDIR /$WORKDIR
ENTRYPOINT ["/entrypoint.sh"]
CMD ["sleep", "infinity"]
