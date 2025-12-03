#!/bin/bash

# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0
FILE=$1
if [[ $FILE == *".yml"* ]] ; then
  docker compose -f $FILE up -d
elif [ -z "$FILE" ] ; then
  docker compose -f platforms.yml up -d
  docker compose -f simulator.yml up -d
  docker compose -f tools.yml up -d
else 
  docker compose -f $FILE.yml up -d 
fi
