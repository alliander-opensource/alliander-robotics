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

# Add NVIDIA Debian packages apt repository:
# https://docs.nvidia.com/jetson/archives/r39.2.1/DeveloperGuide/SD/SoftwarePackagesAndTheUpdateMechanism.html#updating-a-host
RUN apt-key adv --fetch-key https://repo.download.nvidia.com/jetson/jetson-ota-public.asc \
  && if [ $(dpkg --print-architecture) = "amd64" ]; \
  then add-apt-repository -y "deb https://repo.download.nvidia.com/jetson/x86_64/noble r39.2 main" ;\
  elif [ $(dpkg --print-architecture) = "arm64" ]; \ 
  then add-apt-repository -y "deb https://repo.download.nvidia.com/jetson/common r39.2 main" ;\
  else echo "Unsupported architecture: $(dpkg --print-architecture)"; exit 1; fi

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

# Install NVIDIA packages:
RUN apt update && apt install -y ros-${ROS_DISTRO}-isaac-ros-apriltag

# Install alliander packages:
WORKDIR /$WORKDIR/ros
COPY $SRC_DIRECTORY/alliander_core/src/ /$WORKDIR/ros/src
COPY $SRC_DIRECTORY/alliander_apriltag/src/ /$WORKDIR/ros/src
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

