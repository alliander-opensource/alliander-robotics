#!/bin/bash

# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0
CHOICE=$1
docker compose -f $CHOICE.yml down -t 1
