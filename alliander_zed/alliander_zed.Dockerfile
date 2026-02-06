# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0
ARG BASE_IMAGE=ubuntu:latest
FROM $BASE_IMAGE 

ARG COLCON_BUILD_SEQUENTIAL
ENV ROS_DISTRO=jazzy

# Install ZED SDK:
ARG UBUNTU_RELEASE_YEAR=24      
ARG CUDA_MAJOR=12              
ARG CUDA_MINOR=9                
ARG ZED_SDK_MAJOR=5
ARG ZED_SDK_MINOR=0
RUN echo "CUDA Version ${CUDA_MAJOR}.${CUDA_MINOR}.0" > /usr/local/cuda/version.txt || true \
  && installer="ZED_SDK_Ubuntu${UBUNTU_RELEASE_YEAR}_cuda${CUDA_MAJOR}.${CUDA_MINOR}.run" \
  && sdk_url="https://download.stereolabs.com/zedsdk/${ZED_SDK_MAJOR}.${ZED_SDK_MINOR}/cu${CUDA_MAJOR}/ubuntu${UBUNTU_RELEASE_YEAR}" \
  && echo "Downloading ${sdk_url}  →  ${installer} ..." \
  && wget -q --show-progress -O "${installer}" "${sdk_url}" \
  && chmod +x "${installer}" \
  && echo "Running installer …" \
  && ./"${installer}" -- silent \
  && chmod -R u+rwX,go+rX /usr/local/zed \
  && rm -f "${installer}" \
  && rm -rf /var/lib/apt/lists/*

# Install ZED Wrapper:
WORKDIR /rcdt/external
RUN apt update \
  && git clone -b jazzy https://github.com/stereolabs/zed-ros2-wrapper.git src/zed_ros2_wrapper \
  && cd src/zed_ros2_wrapper \
  && git checkout 2efb1a33a40d399b9019165df2400cf3ad682fc5 \
  && cd /rcdt/external \
  && rosdep update --rosdistro $ROS_DISTRO \
  && rosdep install --from-paths src -y -i
RUN /rcdt/colcon_build.sh

# Install repo packages:
WORKDIR /rcdt/ros
COPY alliander_core/src/ /rcdt/ros/src
COPY alliander_zed/src/ /rcdt/ros/src
RUN /rcdt/colcon_build.sh

# Install python dependencies:
COPY pyproject.toml /rcdt/pyproject.toml
RUN uv sync

# Finalize
WORKDIR /rcdt
ENTRYPOINT ["/entrypoint.sh"]
CMD ["sleep", "infinity"]
