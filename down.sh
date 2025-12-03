#!/bin/bash

# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0
FILE=$1
if [[ $FILE == *".yml"* ]] ; then
  docker compose -f $FILE down -t 1
elif [ -z "$FILE" ] ; then
  docker compose -f platforms.yml down -t 1
  docker compose -f simulator.yml down -t 1
  docker compose -f tools.yml down -t 1
else 
  docker compose -f $FILE.yml down -t 1
fi
