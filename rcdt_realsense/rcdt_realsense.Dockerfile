# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0
ARG BASE_IMAGE=ubuntu:latest
FROM $BASE_IMAGE 

ARG COLCON_BUILD_SEQUENTIAL
ENV ROS_DISTRO=jazzy
WORKDIR /rcdt/ros
COPY pyproject.toml /rcdt/pyproject.toml

# Install Realsense SDK:
RUN apt update && apt install -y --no-install-recommends \
  libssl-dev libusb-1.0-0-dev libudev-dev pkg-config libgtk-3-dev \
  git wget cmake build-essential v4l-utils rsync unzip \
  libglfw3-dev libgl1-mesa-dev libglu1-mesa-dev at \
  && rm -rf /var/lib/apt/lists/* \
  && apt autoremove -y \
  && apt clean

ARG ZIP_URL="https://github.com/IntelRealSense/librealsense/releases/download/v2.57.3/librealsense2_jammy_x86_debians_2_57_3_beta.zip"
ARG TEMP_DIR="/tmp/realsense_install"
ARG ZIP_FILE="$TEMP_DIR/librealsense2_jammy_x86_debians_2_57_3_beta.zip"
RUN mkdir -p "$TEMP_DIR" \
  && wget -O "$ZIP_FILE" "$ZIP_URL" \
  && unzip "$ZIP_FILE" -d "$TEMP_DIR" \ 
  && dpkg -i "$TEMP_DIR"/*.deb \
  && rm -rf "$TEMP_DIR"

# Install Realsense Wrapper:
RUN apt update \
  && mkdir -p /rcdt/ros/src \
  && cd /rcdt/ros \
  && git clone -b 4.57.2 https://github.com/IntelRealSense/realsense-ros.git src/realsense_ros \   
  && rosdep update --rosdistro $ROS_DISTRO \
  && rosdep install --from-paths src -y -i

RUN uv sync \
  && . /opt/ros/$ROS_DISTRO/setup.sh \ 
  && colcon build --symlink-install \
  --cmake-args -DCMAKE_BUILD_TYPE=Release \ 
  --event-handlers console_direct+

# Install dev packages
COPY common/dev-pkgs.txt /rcdt/dev-pkgs.txt
RUN apt update && apt install -y -qq --no-install-recommends  \
  `cat /rcdt/dev-pkgs.txt`\
  && rm -rf /var/lib/apt/lists/* \
  && apt autoremove \
  && apt clean

# Install repo packages:
COPY rcdt_description/src/ /rcdt/ros/src
COPY rcdt_realsense/src/ /rcdt/ros/src
RUN . /opt/ros/$ROS_DISTRO/setup.sh \ 
  && colcon build --symlink-install --packages-up-to \
  rcdt_description \
  rcdt_realsense

# Finalize
WORKDIR /rcdt
ENTRYPOINT ["/entrypoint.sh"]
CMD ["sleep", "infinity"]
