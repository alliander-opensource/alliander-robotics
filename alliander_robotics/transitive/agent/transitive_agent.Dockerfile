# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

# Based on: https://github.com/transitiverobotics/example-robot-docker/blob/main/Dockerfile

ARG ROS_DISTRO=jazzy
FROM ros:${ROS_DISTRO}

# Install dependencies. This includes dependencies for webrtc-video and the capabilities using it (e.g., remote-teleop)
RUN apt update && DEBIAN_FRONTEND=noninteractive apt install -y \
  apt-utils iputils-ping curl git lsb-release gnupg vim build-essential \
  pkg-config fontconfig gobject-introspection gstreamer1.0-x gstreamer1.0-libav \
  gstreamer1.0-nice gstreamer1.0-plugins-bad gstreamer1.0-plugins-base-apps \
  gstreamer1.0-plugins-good gstreamer1.0-plugins-ugly gstreamer1.0-tools \
  libgstreamer1.0-0 libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev \
  libgstreamer-plugins-bad1.0-dev libgirepository1.0-dev libc-dev libcairo2 \
  libcairo2-dev avahi-utils

# Install agent:
ADD https://install.transitiverobotics.com?id=placeholder&token=placeholder&docker=true /tmp/install.sh
RUN chmod +x /tmp/install.sh
RUN bash -c ". /opt/ros/${ROS_DISTRO}/setup.bash && /tmp/install.sh"

# We need to clear but not delete the machine-id to avoid duplicate device Ids
RUN echo "" > /etc/machine-id

# Automatically source ROS2:
RUN echo "source /opt/ros/$ROS_DISTRO/setup.bash" >> /root/.bashrc

# Set cyclonedds as RMW implementation:
RUN apt update && apt install -y ros-${ROS_DISTRO}-rmw-cyclonedds-cpp && rm -rf /var/lib/apt/lists/*
ENV RMW_IMPLEMENTATION=rmw_cyclonedds_cpp

# Install additional ROS2 packages:
RUN apt update && apt install -y \
  ros-${ROS_DISTRO}-geographic-msgs \
  && rm -rf /var/lib/apt/lists/*


# Finalize
WORKDIR /root
COPY entrypoint.sh .
ENTRYPOINT ["./entrypoint.sh"]
