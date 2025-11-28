# syntax = devthefuture/dockerfile-x
# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0
ARG BASE_IMAGE=ubuntu:latest
FROM $BASE_IMAGE 

ARG COLCON_BUILD_SEQUENTIAL
ENV ROS_DISTRO=jazzy
ENV ZIP_URL https://github.com/IntelRealSense/librealsense/releases/download/v2.57.3/librealsense2_jammy_x86_debians_2_57_3_beta.zip
ENV TEMP_DIR /tmp/realsense_install
ENV ZIP_FILE $TEMP_DIR/librealsense2_jammy_x86_debians_2_57_3_beta.zip

# Install core dependencies 
RUN apt update && apt install -y --no-install-recommends \
    at \
    libgl1-mesa-dev \
    libglfw3-dev \
    libglu1-mesa-dev \
    libgtk-3-dev \
    libssl-dev \
    libudev-dev \
    libusb-1.0-0-dev \
    pkg-config \
    rsync \
    v4l-utils \
  && rm -rf /var/lib/apt/lists/* \
  && apt autoremove -y \
  && apt clean

# Install librealsense
RUN mkdir -p $TEMP_DIR \
  && wget -O $ZIP_FILE $ZIP_URL \
  && unzip $ZIP_FILE -d $TEMP_DIR \
  && dpkg -i $TEMP_DIR/*.deb \
  && rm -rf $TEMP_DIR

# Install ROS SDK
RUN mkdir -p /rcdt/realsense_ws \
  && cd /rcdt/realsense_ws \
  && git clone -b 4.57.2 https://github.com/IntelRealSense/realsense-ros.git src/realsense_ros \
  && rosdep update --rosdistro $ROS_DISTRO \
  && rosdep install -i --from-path src --rosdistro $ROS_DISTRO --skip-keys=librealsense2 -y

RUN . /opt/ros/$ROS_DISTRO/setup.sh \
  && colcon build  --symlink-install --cmake-args -DCMAKE_BUILD_TYPE=Release \
  && echo "source /rcdt/realsense_ws/install/setup.bash" >>/root/.bashrc

# Install dev packages
COPY dev-pkgs.txt /rcdt/dev-pkgs.txt
RUN apt update && apt install -y -qq --no-install-recommends  \
    `cat /rcdt/dev-pkgs.txt`\
    && rm -rf /var/lib/apt/lists/* \
    && apt autoremove \
    && apt clean

WORKDIR /rcdt
ENTRYPOINT ["/entrypoint.sh"]
CMD ["sleep", "infinity"]
