#!/bin/bash

# SPDX-FileCopyrightText: Alliander N. V.
# 
# SPDX-License-Identifier: Apache-2.0

DIRS=$(ls | grep alliander_ | tr '\n' ' ')
echo "Scanning $DIRS..."

pydoclint *.py $DIRS -q
