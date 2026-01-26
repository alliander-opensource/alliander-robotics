#!/bin/bash

# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

mapfile -t CONTAINER_NAMES < <(docker ps -q | xargs -n 1 docker inspect --format '{{ .Name }}')
mapfile -t CONTAINER_IDS < <(docker ps -q)

echo "Choose Docker container to attach to:"
for i in "${!CONTAINER_NAMES[@]}"; do
  CLEAN_NAME=$(echo "${CONTAINER_NAMES[$i]}" | sed 's/^[\/]//')
  echo "$((i+1)). ${CLEAN_NAME}"
done

stty sane
read -p "Enter container number (1-N): " CHOICE

SELECTED_ID="${CONTAINER_IDS[$((CHOICE-1))]}"
SELECTED_NAME="${CONTAINER_NAMES[$((CHOICE-1))]}"

echo "Attaching to $SELECTED_ID/$SELECTED_NAME"

docker exec -it $SELECTED_NAME bash
