#!/bin/bash -i

# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

set -e
source /home/$UNAME/.bashrc
apt update

mkdir -p /home/$UNAME/osm2world
cd /home/$UNAME/osm2world
wget https://osm2world.org/download/files/latest/OSM2World-latest-bin.zip
unzip OSM2World-latest-bin.zip
rm OSM2World-latest-bin.zip