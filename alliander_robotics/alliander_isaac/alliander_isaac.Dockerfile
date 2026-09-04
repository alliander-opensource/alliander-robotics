# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0
ARG BASE_IMAGE=ubuntu:latest
FROM $BASE_IMAGE AS builder

################################################
# Single stage due to large installs for runtime
################################################

ARG SRC_DIRECTORY
ENV ROS_DISTRO=jazzy

# Add the NVIDIA Cuda apt repository:
# https://docs.nvidia.com/cuda/cuda-installation-guide-linux/#network-repo-installation-for-ubuntu
RUN if [ $(dpkg --print-architecture) = "amd64" ]; \
  then wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2404/x86_64/cuda-keyring_1.1-1_all.deb ; \
  elif [ $(dpkg --print-architecture) = "arm64" ]; \ 
  then wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2404/arm64/cuda-keyring_1.1-1_all.deb ;\
  else echo "Unsupported architecture: $(dpkg --print-architecture)"; exit 1; fi \
  && dpkg -i cuda-keyring_1.1-1_all.deb

# Add the NVIDIA Isaac ROS apt repository:
# https://nvidia-isaac-ros.github.io/getting_started/index.html#configure-isaac-ros-apt-repository
RUN k="/usr/share/keyrings/nvidia-isaac-ros.gpg" \
  && curl -fsSL https://isaac.download.nvidia.com/isaac-ros/repos.key | sudo gpg --dearmor | sudo tee -a $k > /dev/null \
  && f="/etc/apt/sources.list.d/nvidia-isaac-ros.list" \
  && touch $f \
  && if [ $(dpkg --print-architecture) = "amd64" ]; \
  then s="deb [signed-by=$k] https://isaac.download.nvidia.com/isaac-ros/release-4.6 noble main" ; \
  elif [ $(dpkg --print-architecture) = "arm64" ]; \ 
  then s="deb [signed-by=$k] https://isaac.download.nvidia.com/isaac-ros/release-4.6 noble-jetpack main" ; \
  else echo "Unsupported architecture: $(dpkg --print-architecture)"; exit 1; fi \
  && grep -qxF "$s" $f || echo "$s" | sudo tee -a $f

# Add the NVIDIA VPI apt repository:
# https://docs.nvidia.com/vpi/installation.html
RUN apt-key adv --fetch-key https://repo.download.nvidia.com/jetson/jetson-ota-public.asc \
  && add-apt-repository -y 'deb https://repo.download.nvidia.com/jetson/x86_64/noble r39.2 main'

# Install NVIDIA packages:
RUN --mount=type=cache,id=apt-cache,target=/var/cache/apt,sharing=locked --mount=type=cache,id=apt-lists,target=/var/lib/apt,sharing=locked \
  apt update && apt install -y --allow-downgrades ros-${ROS_DISTRO}-isaac-ros-apriltag

# Install alliander packages:
WORKDIR /$WORKDIR/ros
COPY $SRC_DIRECTORY/alliander_core/src/ /$WORKDIR/ros/src
COPY $SRC_DIRECTORY/alliander_isaac/src/ /$WORKDIR/ros/src
RUN --mount=type=cache,id=apt-cache,target=/var/cache/apt,sharing=locked --mount=type=cache,id=apt-lists,target=/var/lib/apt,sharing=locked /$WORKDIR/rosdep_install.sh --build
RUN /$WORKDIR/colcon_build.sh

# Install python dependencies:
WORKDIR $WORKDIR
COPY $SRC_DIRECTORY/pyproject.toml /$WORKDIR/pyproject.toml
RUN --mount=type=cache,id=uv-cache,target=/root/.cache/uv uv sync \
  && echo "export PYTHONPATH=\"$(dirname $(dirname $(uv python find)))/lib/python3.12/site-packages:\$PYTHONPATH\"" >> /root/.bashrc \
  && echo "export PATH=\"$(dirname $(dirname $(uv python find)))/bin:\$PATH\"" >> /root/.bashrc

# Install runtime dependencies
WORKDIR /$WORKDIR/ros
RUN --mount=type=cache,id=apt-cache,target=/var/cache/apt,sharing=locked --mount=type=cache,id=apt-lists,target=/var/lib/apt,sharing=locked /$WORKDIR/rosdep_install.sh --exec

# Finalize
WORKDIR /$WORKDIR
ENTRYPOINT ["/entrypoint.sh"]
CMD ["sleep", "infinity"]

