# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0
ARG BASE_IMAGE=ubuntu:noble
FROM $BASE_IMAGE 

ARG SRC_DIRECTORY
ENV ROS_DISTRO=jazzy
ENV WORKDIR=alliander

# Install basic packages
RUN --mount=type=cache,id=apt-cache,target=/var/cache/apt,sharing=locked --mount=type=cache,id=apt-lists,target=/var/lib/apt,sharing=locked \
  apt update && apt install -y -qq --no-install-recommends \
  bash \
  build-essential \
  clang-tidy \
  curl \
  flake8 \
  git \
  htop \
  iputils-ping \
  nano \
  net-tools \
  python3-pip \
  software-properties-common \
  unzip \
  wget \
  xvfb \
  zstd

# Add ROS2 to apt sources:
RUN add-apt-repository universe \
  && export ROS_APT_SOURCE_VERSION=$(curl -s https://api.github.com/repos/ros-infrastructure/ros-apt-source/releases/latest | grep -F "tag_name" | awk -F\" '{print $4}') \
  && curl --proto "=https" -L -o /tmp/ros2-apt-source.deb "https://github.com/ros-infrastructure/ros-apt-source/releases/download/${ROS_APT_SOURCE_VERSION}/ros2-apt-source_${ROS_APT_SOURCE_VERSION}.$(. /etc/os-release && echo "$VERSION_CODENAME")_all.deb" \
  && dpkg -i /tmp/ros2-apt-source.deb

# Install ROS2
RUN apt update && apt install -y --no-install-recommends \
  ros-"$ROS_DISTRO"-ros-base \
  python3-colcon-common-extensions \
  python3-rosdep \
  python3-vcstool \
  && rm -rf /var/lib/apt/lists/* \
  && apt autoremove -y \
  && apt clean

# Run rosdep
RUN rosdep init && rosdep update

# Install ROS dependencies 
RUN apt update && apt install -y --no-install-recommends \
  ros-"$ROS_DISTRO"-rmw-cyclonedds-cpp \
  ros-"$ROS_DISTRO"-control-msgs \
  ros-"$ROS_DISTRO"-vision-msgs \
  ros-"$ROS_DISTRO"-geographic-msgs \
  ros-"$ROS_DISTRO"-topic-tools \
  && rm -rf /var/lib/apt/lists/* \
  && apt autoremove -y \
  && apt clean

# Install Git LFS
ADD https://packagecloud.io/install/repositories/github/git-lfs/script.deb.sh /tmp/install_git_lfs.sh
RUN bash /tmp/install_git_lfs.sh \
  && apt install -y --no-install-recommends git-lfs \
  && rm -rf /var/lib/apt/lists/* && apt autoremove -y && apt clean

# Install uv
RUN pip install uv==0.12.14 --break-system-packages --only-binary=:all:

# Upgrade CMake:
RUN pip install --upgrade cmake==3.31.6 --break-system-packages --only-binary=:all:

# Prepare ROS workspace for child images
COPY $SRC_DIRECTORY/common/colcon_build.sh /$WORKDIR/colcon_build.sh
COPY $SRC_DIRECTORY/common/rosdep_install.sh /$WORKDIR/rosdep_install.sh
RUN echo 'source /opt/ros/"$ROS_DISTRO"/setup.bash' >> /root/.bashrc

COPY $SRC_DIRECTORY/common/entrypoint.sh /entrypoint.sh
WORKDIR /$WORKDIR
ENTRYPOINT ["/entrypoint.sh"]
CMD ["sleep", "infinity"]
