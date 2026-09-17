#!/bin/sh

# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

set -uo pipefail

# Default environment variables, to be defined in $HOME/rclone.env
RCLONE_READY_DIR="${RCLONE_READY_DIR:-/data/ready}"
RCLONE_REMOTE="${RCLONE_REMOTE:-google_drive_alliander_robotics:default}"
RCLONE_LOG_LEVEL="${RCLONE_LOG_LEVEL:-INFO}"
RCLONE_FILE_AGE_SECONDS="${RCLONE_FILE_AGE_SECONDS:-10}"
RESCAN_INTERVAL_SECONDS="${RESCAN_INTERVAL_SECONDS:-300}"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"
}

upload_files() {
    if rclone move "$RCLONE_READY_DIR" "$RCLONE_REMOTE" \
            --delete-empty-src-dirs \
            --min-age "$RCLONE_FILE_AGE_SECONDS"s \
            --log-level "$RCLONE_LOG_LEVEL" \
            --retries 5 \
            --low-level-retries 10; then
        log "upload complete"
    else
        log "upload FAILED (will retry on next sweep)"
    fi
}

mkdir -p "$RCLONE_READY_DIR"
log "watching $RCLONE_READY_DIR -> $RCLONE_REMOTE (rescan every ${RESCAN_INTERVAL_SECONDS}s)"

while true; do
    sleep "$RESCAN_INTERVAL_SECONDS"
    upload_files
done
