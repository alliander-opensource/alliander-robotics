# syntax = devthefuture/dockerfile-x
# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0
ARG BASE_IMAGE=ubuntu:latest
FROM $BASE_IMAGE 

ARG TARGETARCH
ARG COLCON_BUILD_SEQUENTIAL
ENV ROS_DISTRO=jazzy

ENV UBUNTU_RELEASE_YEAR=24      
ENV CUDA_MAJOR=12              
ENV CUDA_MINOR=9                
ENV ZED_SDK_MAJOR=5
ENV ZED_SDK_MINOR=0             

# Install ROS dependencies 
RUN apt install -y --no-install-recommends \
    ros-$ROS_DISTRO-realsense2-camera \
    ros-$ROS_DISTRO-realsense2-description \
  && rm -rf /var/lib/apt/lists/* \
  && apt autoremove -y \
  && apt clean

# Exit early if arm64 -- support for ZED SDK in arm64 is not added here yet
RUN if [ "$TARGETARCH" = "arm64" ]; then \
        echo "ZED SDK is not available (yet) for Ubuntu 24.04 on arm64. Please run again with amd64 base image."; \
        exit 1; \
    fi

# Download and install ZED SDK 
RUN echo "CUDA Version ${CUDA_MAJOR}.${CUDA_MINOR}.0" > /usr/local/cuda/version.txt || true \
  && installer="ZED_SDK_Ubuntu${UBUNTU_RELEASE_YEAR}_cuda${CUDA_MAJOR}.${CUDA_MINOR}.run" \
  && sdk_url="https://download.stereolabs.com/zedsdk/${ZED_SDK_MAJOR}.${ZED_SDK_MINOR}/cu${CUDA_MAJOR}/ubuntu${UBUNTU_RELEASE_YEAR}" \
  && echo "Downloading ${sdk_url}  →  ${installer} ..." \
  && wget -q -O "${installer}" "${sdk_url}" \
  && chmod +x "${installer}" \
  && echo "Running installer …" \
  && ./"${installer}" -- silent \
  && chmod -R u+rwX,go+rX /usr/local/zed \
  && rm -f "${installer}" \
  && rm -rf /var/lib/apt/lists/*

RUN . /root/.bashrc \
  && cd /rcdt \
  && mkdir zed_ws \
  && cd /rcdt/zed_ws \
  && git clone -b jazzy https://github.com/stereolabs/zed-ros2-wrapper.git src/zed_ros2_wrapper \
  && apt update \
  && rosdep update \
  && rosdep install --from-paths src --rosdistro $ROS_DISTRO -y -r

RUN . /opt/ros/$ROS_DISTRO/setup.sh \
  && colcon build --symlink-install --cmake-args=-DCMAKE_BUILD_TYPE=Release \
  && echo "source /rcdt/zed_ws/install/setup.bash" >>/root/.bashrc

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
