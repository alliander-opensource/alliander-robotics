# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0
ARG BASE_IMAGE=ubuntu:latest
FROM $BASE_IMAGE 

ARG COLCON_BUILD_SEQUENTIAL
ENV ROS_DISTRO=jazzy
ENV WORKDIR=alliander

# Install basic packages & add ROS2 to apt sources
RUN apt update && apt install -y -qq --no-install-recommends \
  bash \
  build-essential \
  curl \
  flake8 \
  git \
  htop \
  iputils-ping \
  nano \
  net-tools \
  python3-pip \
  software-properties-common \
  wget \
  xvfb \
  zstd \
  && add-apt-repository universe \
  && export ROS_APT_SOURCE_VERSION=$(curl -s https://api.github.com/repos/ros-infrastructure/ros-apt-source/releases/latest | grep -F "tag_name" | awk -F\" '{print $4}') \
  && curl -L -o /tmp/ros2-apt-source.deb "https://github.com/ros-infrastructure/ros-apt-source/releases/download/${ROS_APT_SOURCE_VERSION}/ros2-apt-source_${ROS_APT_SOURCE_VERSION}.$(. /etc/os-release \
  && echo $VERSION_CODENAME)_all.deb" \
  && dpkg -i /tmp/ros2-apt-source.deb

# Install ROS2 - maybe ros-base or ROS base image
RUN apt update && apt install -y --no-install-recommends \
  ros-$ROS_DISTRO-desktop \
  python3-colcon-common-extensions \
  python3-rosdep \
  python3-vcstool \
  && rm -rf /var/lib/apt/lists/* \
  && apt autoremove -y \
  && apt clean

# Run rosdep
RUN rosdep init \
  && rosdep update

# Install ROS dependencies 
RUN apt update && apt install -y --no-install-recommends \
  ros-$ROS_DISTRO-rmw-cyclonedds-cpp \
  ros-$ROS_DISTRO-control-msgs \
  ros-$ROS_DISTRO-vision-msgs \
  ros-$ROS_DISTRO-vision-msgs \
  ros-$ROS_DISTRO-geographic-msgs \
  ros-$ROS_DISTRO-topic-tools \
  && rm -rf /var/lib/apt/lists/* \
  && apt autoremove -y \
  && apt clean

# Install Git LFS
RUN apt update \
  && curl -s https://packagecloud.io/install/repositories/github/git-lfs/script.deb.sh | bash \
  && apt install -y --no-install-recommends \
  git-lfs \
  && rm -rf /var/lib/apt/lists/* \
  && apt autoremove -y \
  && apt clean

# Install uv
RUN pip install uv --break-system-packages

# Prepare ROS workspace for child images
COPY common/colcon_build.sh /$WORKDIR/colcon_build.sh
RUN echo "source /opt/ros/$ROS_DISTRO/setup.bash" >> /root/.bashrc

COPY entrypoint.sh /entrypoint.sh
WORKDIR /$WORKDIR
ENTRYPOINT ["/entrypoint.sh"]
CMD ["sleep", "infinity"]
