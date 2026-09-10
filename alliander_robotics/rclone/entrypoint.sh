#!/bin/bash

# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

set -uo pipefail  # no -e: one failed upload shouldn't kill the loop

READY_DIR="${READY_DIR:-/data/ready}"
REMOTE="${RCLONE_REMOTE:-google_drive_alliander_robotics:laptop_rosalie}"
LOG_LEVEL="${RCLONE_LOG_LEVEL:-INFO}"
STABLE_WAIT="${STABLE_WAIT_SECONDS:-5}"  # fallback-only: how long a dir must be unchanged before we trust it
RESCAN_INTERVAL="${RESCAN_INTERVAL_SECONDS:-300}"  # periodic sweep: retries failures, catches any missed inotify event

log() {
    printf '%s %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*";
}
 
fingerprint() {
    find "$1" -type f -printf '%T@ %s %p\n' 2>/dev/null | sort
}
 
is_stable() {
    local path="$1" before after

    before="$(fingerprint "$path")"
    sleep "$STABLE_WAIT"
    after="$(fingerprint "$path")"

    [ "$before" = "$after" ]
}
 
upload_one() {
    local path="$1"
    local relative_path

    [ -e "$path" ] || return 0

    relative_path="${path#"$READY_DIR"/}"

    if [ -d "$path" ]; then
        is_stable "$path" || {
            log "skip (still changing): $relative_path"
            return 0
        }
    else
        # For individual files, wait briefly and make sure they still exist
        # with the same size/mtime.
        is_stable "$(dirname "$path")" || {
            log "skip (directory still changing): $relative_path"
            return 0
        }
    fi

    log "uploading: $relative_path -> $REMOTE/$relative_path"

    if rclone move "$path" "$REMOTE/$relative_path" \
            --delete-empty-src-dirs \
            --log-level "$LOG_LEVEL" \
            --retries 5 \
            --low-level-retries 10; then
        log "done: $relative_path"
    else
        log "FAILED (will retry on next sweep): $relative_path"
    fi
}
 
scan_and_upload() {
    local item
    for item in "$READY_DIR"/*; do
        [ -e "$item" ] || continue
        upload_one "$item"
    done
}

mkdir -p "$READY_DIR"
log "watching $READY_DIR -> $REMOTE (rescan every ${RESCAN_INTERVAL}s)"
 
# Periodic sweep:
# - retries failed uploads
# - catches anything missed by inotify
(
    while true; do
        sleep "$RESCAN_INTERVAL"
        scan_and_upload
    done
) &

# Upload anything that was already present when we started.
scan_and_upload

# Watch for new files/directories arriving in /data/ready.
inotifywait -m -q \
    -e create \
    -e moved_to \
    --format '%f' \
    "$READY_DIR" |
while read -r name; do
  upload_one "$READY_DIR/$name"
done
 
wait
