# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0
ARG BASE_IMAGE=ubuntu:latest
FROM $BASE_IMAGE 

ARG COLCON_BUILD_SEQUENTIAL
ENV ROS_DISTRO=jazzy

# Install ZED SDK:
ARG TEMP_DIR="/tmp/zed_install"
ARG RUN_FILE="$TEMP_DIR/zed_sdk.run"
RUN mkdir -p "$TEMP_DIR"
RUN if [ $(dpkg --print-architecture) = "amd64" ]; \
  then wget -O "$RUN_FILE" "https://stereolabs.sfo2.cdn.digitaloceanspaces.com/zedsdk/5.0/ZED_SDK_Ubuntu24_cuda12.8_tensorrt10.9_v5.0.7.zstd.run"; \
  elif [ $(dpkg --print-architecture) = "arm64" ]; \ 
  then wget -O "$RUN_FILE" "https://stereolabs.sfo2.cdn.digitaloceanspaces.com/zedsdk/5.0/ZED_SDK_Tegra_L4T36.4_v5.0.7.zstd.run"; \
  else echo "Unsupported architecture: $(dpkg --print-architecture)"; exit 1; fi
RUN chmod +x "${RUN_FILE}" \
  && "${RUN_FILE}" -- silent \
  && chmod -R u+rwX,go+rX /usr/local/zed \
  && rm -f "${RUN_FILE}" \
  && rm -rf /var/lib/apt/lists/*

# Install ZED Wrapper:
WORKDIR /$WORKDIR/external
RUN apt update \
  && git clone -b humble-v5.0.0 https://github.com/stereolabs/zed-ros2-wrapper.git src/zed_ros2_wrapper \
  && cd /$WORKDIR/external \
  && rosdep update --rosdistro $ROS_DISTRO \
  && rosdep install --from-paths src -y -i
RUN /$WORKDIR/colcon_build.sh

# Install repo packages:
WORKDIR /$WORKDIR/ros
COPY alliander_robotics/alliander_core/src/ /$WORKDIR/ros/src
COPY alliander_robotics/alliander_zed/src/ /$WORKDIR/ros/src
RUN /$WORKDIR/colcon_build.sh

# Install python dependencies:
WORKDIR $WORKDIR
COPY pyproject.toml /$WORKDIR/pyproject.toml
RUN uv sync \
  && echo "export PYTHONPATH=\"$(dirname $(dirname $(uv python find)))/lib/python3.12/site-packages:\$PYTHONPATH\"" >> /root/.bashrc \
  && echo "export PATH=\"$(dirname $(dirname $(uv python find)))/bin:\$PATH\"" >> /root/.bashrc

# Finalize
WORKDIR /$WORKDIR
ENTRYPOINT ["/entrypoint.sh"]
CMD ["sleep", "infinity"]
