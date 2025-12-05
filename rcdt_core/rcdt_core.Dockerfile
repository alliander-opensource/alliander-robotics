# syntax = devthefuture/dockerfile-x
# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0
ARG BASE_IMAGE=ubuntu:latest
FROM $BASE_IMAGE 

ARG COLCON_BUILD_SEQUENTIAL
ENV ROS_DISTRO=jazzy

# Create bashrc file:
RUN mkdir /rcdt \
  && echo "if test -f ~/.personal.bashrc; then\nsource ~/.personal.bashrc\nfi" >> /root/.bashrc \
  && echo "if test -f ~/.env; then\nset -a && source ~/.env && set +a\nfi" >> /root/.bashrc

# Install basic packages & add ROS2 to apt sources
RUN apt update && apt install -y -qq --no-install-recommends \
  bash \
  build-essential \
  curl \
  flake8 \
  git \
  htop \
  nano \
  python3-pip \
  software-properties-common \
  wget \
  zstd \
  && add-apt-repository universe \
  && export ROS_APT_SOURCE_VERSION=$(curl -s https://api.github.com/repos/ros-infrastructure/ros-apt-source/releases/latest | grep -F "tag_name" | awk -F\" '{print $4}') \
&& curl -L -o /tmp/ros2-apt-source.deb "https://github.com/ros-infrastructure/ros-apt-source/releases/download/${ROS_APT_SOURCE_VERSION}/ros2-apt-source_${ROS_APT_SOURCE_VERSION}.$(. /etc/os-release \
&& echo $VERSION_CODENAME)_all.deb" \
&& dpkg -i /tmp/ros2-apt-source.deb

# Install ROS2
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
    ros-$ROS_DISTRO-launch-pytest \
    ros-$ROS_DISTRO-rmw-cyclonedds-cpp \
    ros-$ROS_DISTRO-vision-msgs \
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

# Python dependencies
RUN pip install uv --break-system-packages
RUN echo "export PYTHONPATH=\"/rcdt/.venv/lib/python3.12/site-packages:\$PYTHONPATH\"" \
  >> /root/.bashrc \
  && echo "export PATH=\"/rcdt/.venv/bin:\$PATH\"" \
  >> /root/.bashrc

# Copy custom packages & dependency list
RUN mkdir -p /rcdt/ros/
COPY rcdt_core/src/ /rcdt/ros/src
COPY pyproject.toml /rcdt/pyproject.toml

# Build basic packages 
RUN cd /rcdt/ros \
  && uv sync \
  && . /opt/ros/$ROS_DISTRO/setup.sh \ 
  && colcon build --symlink-install \
  --cmake-args -DCMAKE_BUILD_TYPE=Release \ 
  --event-handlers console_direct+ \
  && echo "source /opt/ros/$ROS_DISTRO/setup.bash" >> /root/.bashrc \
  && echo "source /rcdt/ros/install/setup.bash" >> /root/.bashrc

COPY entrypoint.sh /entrypoint.sh

WORKDIR /rcdt
ENTRYPOINT ["/entrypoint.sh"]
CMD ["sleep", "infinity"]
