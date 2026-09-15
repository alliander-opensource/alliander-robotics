# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0
ARG BASE_IMAGE=ubuntu:noble
FROM $BASE_IMAGE AS builder

##############################
# Build stage
##############################

ARG SRC_DIRECTORY
ENV ROS_DISTRO=jazzy

# Install L3Cam SDK:
ARG TEMP_DIR="/tmp/beamagine_install"
ARG RUN_FILE="$TEMP_DIR/l3cam_sdk.run"
RUN mkdir -p "$TEMP_DIR"
RUN if [ $(dpkg --print-architecture) = "amd64" ]; \
  then wget -O "$RUN_FILE" "https://github.com/beamaginelidar/libl3cam/releases/download/0.2.1R/libl3cam_0.2.1-1_amd64.deb"; \
  elif [ $(dpkg --print-architecture) = "arm64" ]; \
  then wget -O "$RUN_FILE" "https://github.com/beamaginelidar/libl3cam/releases/download/0.2.1R/libl3cam_0.2.1-1_arm64.deb"; \
  else echo "Unsupported architecture: $(dpkg --print-architecture)"; exit 1; fi
RUN dpkg -i "${RUN_FILE}"

# Set buffer size:
RUN echo 'net.core.rmem_default=268435456' >> /etc/sysctl.conf && \
  echo 'net.core.rmem_max=268435456' >> /etc/sysctl.conf && \
  echo 'net.core.netdev_max_backlog=5000' >> /etc/sysctl.conf

# Install external packages:
WORKDIR /$WORKDIR/external
RUN git clone -b jazzy https://github.com/alliander-robotics/l3cam_ros2.git src/l3cam_ros2
RUN --mount=type=cache,id=apt-cache,target=/var/cache/apt,sharing=locked --mount=type=cache,id=apt-lists,target=/var/lib/apt,sharing=locked /"$WORKDIR"/rosdep_install.sh --build
RUN /"$WORKDIR"/colcon_build.sh --external

# Install alliander packages:
WORKDIR /$WORKDIR/ros
COPY $SRC_DIRECTORY/alliander_core/src/ /$WORKDIR/ros/src
COPY $SRC_DIRECTORY/alliander_beamagine/src/ /$WORKDIR/ros/src
COPY $SRC_DIRECTORY/utilities/depth_camera/ /$WORKDIR/ros/src/depth_camera
RUN --mount=type=cache,id=apt-cache,target=/var/cache/apt,sharing=locked --mount=type=cache,id=apt-lists,target=/var/lib/apt,sharing=locked /"$WORKDIR"/rosdep_install.sh --build
RUN /"$WORKDIR"/colcon_build.sh

# Install python dependencies:
WORKDIR $WORKDIR
COPY $SRC_DIRECTORY/pyproject.toml /$WORKDIR/pyproject.toml
RUN --mount=type=cache,id=uv-cache,target=/root/.cache/uv uv lock \
  && uv sync --frozen --no-build \
  && cat <<EOF >> /root/.bashrc
export PYTHONPATH="$(dirname $(dirname $(uv python find)))/lib/python3.12/site-packages:\$PYTHONPATH"
export PATH="$(dirname $(dirname $(uv python find)))/bin:\$PATH"
EOF

##############################
# Runtime stage
##############################

FROM ${BASE_IMAGE}
ENV ROS_DISTRO=jazzy

# Copy environments
COPY --from=builder /$WORKDIR/.venv /$WORKDIR/.venv
COPY --from=builder /root/.bashrc /root/.bashrc
COPY --from=builder /etc/sysctl.conf /etc/sysctl.conf

# Copy external packages and install runtime dependencies:
WORKDIR /$WORKDIR/external
COPY --from=builder /$WORKDIR/external /$WORKDIR/external
RUN --mount=type=cache,id=apt-cache,target=/var/cache/apt,sharing=locked --mount=type=cache,id=apt-lists,target=/var/lib/apt,sharing=locked /"$WORKDIR"/rosdep_install.sh --exec
RUN rm -rf src build log

# Copy alliander packages and install runtime dependencies:
WORKDIR /$WORKDIR/ros
COPY --from=builder /$WORKDIR/ros /$WORKDIR/ros
RUN --mount=type=cache,id=apt-cache,target=/var/cache/apt,sharing=locked --mount=type=cache,id=apt-lists,target=/var/lib/apt,sharing=locked /"$WORKDIR"/rosdep_install.sh --exec

# Finalize
WORKDIR /$WORKDIR
ENTRYPOINT ["/entrypoint.sh"]
CMD ["sleep", "infinity"]
