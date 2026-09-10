# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0

FROM rclone/rclone:latest

RUN apk add --no-cache bash findutils inotify-tools tzdata

COPY --chmod=0755 entrypoint.sh /usr/local/bin/rclone_filesync/entrypoint.sh

ENTRYPOINT ["/usr/local/bin/rclone_filesync/entrypoint.sh"]
WORKDIR /