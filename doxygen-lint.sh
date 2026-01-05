#!/bin/bash

# SPDX-FileCopyrightText: Alliander N. V.
# 
# SPDX-License-Identifier: Apache-2.0
FILENAME=doxyfile.lint

if ! command -v doxygen > /dev/null 2>&1 ; then
  echo "Doxygen not found, exiting."
  exit 1
fi

if [ ! -f $FILENAME ]; then
  echo "Doxyfile '$FILENAME' not found, exiting."
  exit 1
fi

OUTPUT=$(doxygen $FILENAME /dev/null 2>&1)
NUM_WARNINGS=$(echo "$OUTPUT" | grep -i "warning:" | wc -l)

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)
rm -rf $SCRIPT_DIR/html/

if [ "$NUM_WARNINGS" -gt 0 ]; then
  echo "$OUTPUT"
  echo "Doxygen found $NUM_WARNINGS documentation warnings."
  exit 1
fi
