# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0
ARG BASE_IMAGE=ubuntu:latest
FROM $BASE_IMAGE 

ARG COLCON_BUILD_SEQUENTIAL
ENV ROS_DISTRO=jazzy

ENV RUSTUP_HOME=/root/rustup
ENV CARGO_HOME=/root/cargo

# Install Rust
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y

ENV PATH="/root/cargo/bin:${PATH}"

# Install ROS dependencies 
RUN apt update && apt install -y --no-install-recommends \
  ros-$ROS_DISTRO-velodyne-description \
  ros-$ROS_DISTRO-pointcloud-to-laserscan \
  && rm -rf /var/lib/apt/lists/* \
  && apt autoremove -y \
  && apt clean

# Install core packages:
WORKDIR /$WORKDIR/ros
COPY alliander_core/src/ /$WORKDIR/ros/src
RUN /$WORKDIR/colcon_build.sh

# Install repo package:
WORKDIR $WORKDIR
RUN mkdir -p /$WORKDIR/rust/
COPY alliander_seekthermal/src/ /$WORKDIR/rust/
WORKDIR /$WORKDIR/rust/alliander_seekthermal/
RUN . /opt/ros/jazzy/setup.sh && cargo build

# Install python dependencies:
WORKDIR $WORKDIR
COPY pyproject.toml /$WORKDIR/pyproject.toml
RUN uv sync \
  && echo "export PYTHONPATH=\"$(dirname $(dirname $(uv python find)))/lib/python3.12/site-packages:\$PYTHONPATH\"" >> /root/.bashrc \
  && echo "export PATH=\"$(dirname $(dirname $(uv python find)))/bin:\$PATH\"" >> /root/.bashrc

# Finalize
WORKDIR /$WORKDIR
ENTRYPOINT ["/entrypoint.sh"]
CMD ["sleep", "infinity"]
