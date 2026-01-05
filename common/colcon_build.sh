# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0
#!/bin/bash
set -e

cd /rcdt/ros
uv sync
. /opt/ros/$ROS_DISTRO/setup.sh
colcon build --symlink-install \
  --cmake-args -DCMAKE_BUILD_TYPE=Release 

echo "source /opt/ros/$ROS_DISTRO/setup.bash" >> /root/.bashrc
echo "source /rcdt/ros/install/setup.bash" >> /root/.bashrc
