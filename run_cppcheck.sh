#!/bin/bash
# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0
set -e
cppcheck \
  --suppressions-list=.cppcheck-suppressions \
  --enable=warning,performance,portability,style \
  --error-exitcode=1 \
  $(find . -name *.cpp)

