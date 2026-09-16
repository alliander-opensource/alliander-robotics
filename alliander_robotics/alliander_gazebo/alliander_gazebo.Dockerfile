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

# Install osm2world
ADD https://osm2world.org/download/files/latest/OSM2World-latest-bin.zip /tmp/OSM2World-latest-bin.zip
RUN mkdir -p /"$WORKDIR"/osm2world \
  && cd /"$WORKDIR"/osm2world \
  && unzip /tmp/OSM2World-latest-bin.zip

# Install external packages:
WORKDIR /$WORKDIR/external
COPY $SRC_DIRECTORY/common/get_vendor_descriptions.py /$WORKDIR/get_vendor_descriptions.py
RUN python3 /"$WORKDIR"/get_vendor_descriptions.py
RUN --mount=type=cache,id=apt-cache,target=/var/cache/apt,sharing=locked --mount=type=cache,id=apt-lists,target=/var/lib/apt,sharing=locked /"$WORKDIR"/rosdep_install.sh --build
RUN /"$WORKDIR"/colcon_build.sh --external

# Install alliander packages:
WORKDIR /$WORKDIR/ros
COPY $SRC_DIRECTORY/alliander_core/src/ /$WORKDIR/ros/src
COPY $SRC_DIRECTORY/alliander_gazebo/src/ /$WORKDIR/ros/src
RUN --mount=type=cache,id=apt-cache,target=/var/cache/apt,sharing=locked --mount=type=cache,id=apt-lists,target=/var/lib/apt,sharing=locked /"$WORKDIR"/rosdep_install.sh --build
RUN /"$WORKDIR"/colcon_build.sh

# Install python dependencies:
WORKDIR $WORKDIR
COPY $SRC_DIRECTORY/pyproject.toml /$WORKDIR/pyproject.toml
RUN --mount=type=cache,id=uv-cache,target=/root/.cache/uv uv lock \
  && uv sync --frozen --no-build --group alliander-gazebo \
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
COPY --from=builder /$WORKDIR/osm2world /$WORKDIR/osm2world

# Install java runtime for OSM2World:
RUN --mount=type=cache,id=apt-cache,target=/var/cache/apt,sharing=locked --mount=type=cache,id=apt-lists,target=/var/lib/apt,sharing=locked \
  apt update && apt install -y --no-install-recommends openjdk-17-jre

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
