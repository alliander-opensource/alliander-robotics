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

# Install external packages:
WORKDIR /"$WORKDIR"/external
RUN git clone --depth=1 --filter=blob:none -b v3.1.1 https://github.com/frankarobotics/franka_ros2.git src/franka_ros2 \
    && cd src/franka_ros2 && git sparse-checkout set franka_msgs
# Install newer version of launch_testing from source, to solve conflict with pytest: https://github.com/ros2/launch/pull/972
RUN git clone --depth=1 --filter=blob:none -b 3.10.0 https://github.com/ros2/launch.git src/launch \
    && cd src/launch && git sparse-checkout set launch_testing 
RUN --mount=type=cache,id=apt-cache,target=/var/cache/apt,sharing=locked --mount=type=cache,id=apt-lists,target=/var/lib/apt,sharing=locked /"$WORKDIR"/rosdep_install.sh --build
RUN /"$WORKDIR"/colcon_build.sh --external

# # Install alliander packages:
WORKDIR /"$WORKDIR"/ros
COPY $SRC_DIRECTORY/alliander_core/src/ /"$WORKDIR"/ros/src
COPY $SRC_DIRECTORY/alliander_tests/src/ /"$WORKDIR"/ros/src
RUN --mount=type=cache,id=apt-cache,target=/var/cache/apt,sharing=locked --mount=type=cache,id=apt-lists,target=/var/lib/apt,sharing=locked /"$WORKDIR"/rosdep_install.sh --build
RUN /"$WORKDIR"/colcon_build.sh

# Install python dependencies:
WORKDIR "$WORKDIR"
COPY $SRC_DIRECTORY/pyproject.toml /"$WORKDIR"/pyproject.toml
RUN --mount=type=cache,id=uv-cache,target=/root/.cache/uv uv lock && uv sync --frozen --no-build --all-groups \
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
COPY --from=builder /"$WORKDIR"/.venv /"$WORKDIR"/.venv
COPY --from=builder /root/.bashrc /root/.bashrc

# Install tools:
ADD https://get.docker.com /tmp/get-docker.sh
RUN bash /tmp/get-docker.sh

ADD https://raw.githubusercontent.com/rhysd/actionlint/main/scripts/download-actionlint.bash /tmp/download-actionlint.bash
RUN bash /tmp/download-actionlint.bash latest /usr/bin

RUN --mount=type=cache,id=apt-cache,target=/var/cache/apt,sharing=locked --mount=type=cache,id=apt-lists,target=/var/lib/apt,sharing=locked \
    apt update && apt install -y --no-install-recommends \
    clang \
    doxygen \
    reuse

# Copy external packages and install runtime dependencies:
WORKDIR /"$WORKDIR"/external
COPY --from=builder /"$WORKDIR"/external /"$WORKDIR"/external
RUN --mount=type=cache,id=apt-cache,target=/var/cache/apt,sharing=locked --mount=type=cache,id=apt-lists,target=/var/lib/apt,sharing=locked /"$WORKDIR"/rosdep_install.sh --exec
RUN rm -rf src build log

# Copy alliander packages and install runtime dependencies:
WORKDIR /"$WORKDIR"/ros
COPY --from=builder /"$WORKDIR"/ros /"$WORKDIR"/ros
RUN --mount=type=cache,id=apt-cache,target=/var/cache/apt,sharing=locked --mount=type=cache,id=apt-lists,target=/var/lib/apt,sharing=locked /"$WORKDIR"/rosdep_install.sh --exec

WORKDIR /"$WORKDIR"
ENTRYPOINT ["/entrypoint.sh"]
CMD ["sleep", "infinity"]
