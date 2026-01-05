# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0
ARG BASE_IMAGE=ubuntu:latest
FROM $BASE_IMAGE 

ARG COLCON_BUILD_SEQUENTIAL
ENV ROS_DISTRO=jazzy

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
WORKDIR /rcdt/ros
RUN apt update \
  && git clone -b 4.57.2 https://github.com/IntelRealSense/realsense-ros.git src/realsense_ros \   
  && rosdep update --rosdistro $ROS_DISTRO \
  && rosdep install --from-paths src -y -i

# Install repo packages:
COPY pyproject.toml /rcdt/pyproject.toml
COPY rcdt_core/src/ /rcdt/ros/src
COPY rcdt_realsense/src/ /rcdt/ros/src
COPY common/colcon_build.sh /rcdt/colcon_build.sh
RUN /rcdt/colcon_build.sh

# Finalize
WORKDIR /rcdt
ENTRYPOINT ["/entrypoint.sh"]
CMD ["sleep", "infinity"]
