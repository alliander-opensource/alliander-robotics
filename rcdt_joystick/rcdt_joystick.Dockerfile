# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0
ARG BASE_IMAGE=ubuntu:latest
FROM $BASE_IMAGE 

ARG COLCON_BUILD_SEQUENTIAL
ENV ROS_DISTRO=jazzy

# Install repo packages:
WORKDIR /rcdt/ros
COPY rcdt_core/src/ /rcdt/ros/src
COPY rcdt_joystick/src/ /rcdt/ros/src
RUN /rcdt/colcon_build.sh

# Install python dependencies:
COPY pyproject.toml /rcdt/pyproject.toml
RUN uv sync  --all-groups

WORKDIR /rcdt
ENTRYPOINT ["/entrypoint.sh"]
CMD ["sleep", "infinity"]
