#!/bin/bash

# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

set -uo pipefail  # no -e: one failed upload shouldn't kill the loop

# Default environment variables, should be defined in $HOME/rclone.env
READY_DIR="${READY_DIR:-/data/ready}"
RCLONE_REMOTE="${RCLONE_REMOTE:-google_drive_alliander_robotics:default}"
RCLONE_LOG_LEVEL="${RCLONE_LOG_LEVEL:-INFO}"
STABLE_WAIT_SECONDS="${STABLE_WAIT_SECONDS:-5}"
RESCAN_INTERVAL_SECONDS="${RESCAN_INTERVAL_SECONDS:-300}"

log() {
    printf '%s %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*";
}
 
fingerprint() {
    find "$1" -type f -printf '%T@ %s %p\n' 2>/dev/null | sort
}
 
is_stable() {
    local path="$1" before after

    before="$(fingerprint "$path")"
    sleep "$STABLE_WAIT_SECONDS"
    after="$(fingerprint "$path")"

    [ "$before" = "$after" ]
}
 
upload_file() {
    local path="$1"
    local relative_path
    local parent_relative
    local remote_parent

    [ -e "$path" ] || return 0

    relative_path="${path#"$READY_DIR"/}"

    if [ -d "$path" ]; then
        # Directory: preserve the directory itself and its full structure.
        if ! is_stable "$path"; then
            log "skip (still changing): $relative_path"
            return 0
        fi

        log "uploading directory: $relative_path -> $RCLONE_REMOTE/$relative_path"

        if rclone move "$path" "$RCLONE_REMOTE/$relative_path" \
                --delete-empty-src-dirs \
                --log-level "$RCLONE_LOG_LEVEL" \
                --retries 5 \
                --low-level-retries 10; then
            log "done: $relative_path"
        else
            log "FAILED (will retry on next sweep): $relative_path"
        fi

    else
        # File: preserve its path relative to RCLONE_READY_DIR.
        log "uploading file: $relative_path -> $RCLONE_REMOTE/$relative_path"

        if rclone moveto "$path" "$RCLONE_REMOTE/$relative_path" \
                --log-level "$RCLONE_LOG_LEVEL" \
                --retries 5 \
                --low-level-retries 10; then
            log "done: $relative_path"
        else
            log "FAILED (will retry on next sweep): $relative_path"
        fi
    fi
}
 
scan_and_upload() {
    local item
    for item in "$RCLONE_READY_DIR"/*; do
        [ -e "$item" ] || continue
        upload_file "$item"
    done
}

mkdir -p "$RCLONE_READY_DIR"
log "watching $RCLONE_READY_DIR -> $RCLONE_REMOTE (rescan every ${RESCAN_INTERVAL_SECONDS}s)"
 
# Periodic sweep:
# - retries failed uploads
# - catches anything missed by inotify
(
    while true; do
        sleep "$RESCAN_INTERVAL_SECONDS"
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
    "$RCLONE_READY_DIR" |
while read -r name; do
  upload_file "$RCLONE_READY_DIR/$name"
done
 
wait
