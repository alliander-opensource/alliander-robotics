<!--
SPDX-FileCopyrightText: Alliander N. V.

SPDX-License-Identifier: Apache-2.0
-->

# Rclone

According to the official website:

"*Rclone is a command-line program to manage files on cloud storage. It is a feature-rich alternative to cloud vendors' web storage interfaces. Over 70 cloud storage products support rclone including S3 object stores, business & consumer file storage services, as well as standard transfer protocols.*

*Rclone has powerful cloud equivalents to the unix commands rsync, cp, mv, mount, ls, ncdu, tree, rm, and cat.*"

With this tool we can automatically move all files in a specific folder that is located locally on the robot to Google Drive, as well as easily add other custom functionalities for our use-cases.

Additionally, Rclone supports a wide range of providers, which allows us to easily switch between providers without having to adjust the functionality of the file upload itself, making this a future-proof choice.

## Configuration
Rclone needs to be configured locally on the computer, for which [this guide](https://rclone.org/drive/#configuration) can be followed.

The configuration requires getting a token from Google drive. If this token has not been created yet, follow [this guide](https://rclone.org/drive/#making-your-own-client-id) to set up a `client_id`. Note that although the instructions include a step where one should publish the app, it is not actually required to do this.
Find the `client_id` back at:
> [Google Cloud](https://console.cloud.google.com/) > APIs & Services >
*select the project that contains the client ID at the top of the page* >
Credentials >
*select the client under* OAuth 2.0 Client IDs >
Clients > Additional information (> Client secrets)

Possibly a message appears that downloading the client secrets is no longer available. In case of a lost secret, a new one needs to be created.

When Rclone has been correctly configured, `$HOME/.config/rclone/rclone.conf` should exist with at least the following contents:

```conf
[<rclone_configured_name>]
type = drive
client_id = <client_id>
client_secret = <client_secret>
scope = drive
token = {"access_token":"...","token_type":"...","refresh_token":"...","expiry":"..."}
team_drive =
```

## Docker Setup

To activate the Rclone file synchronisation task, one requires to activate the corresponding docker container. The `rclone_filesync` docker container in our repository contains this functionality. This container expects a `rclone.env` file in the home directory of the host device with the following content:

```env
# Filesync configuration
RCLONE_READY_DIR=<data_ready_directory_path>
RCLONE_REMOTE=<rclone_configured_name:unique_robot_name>
RCLONE_LOG_LEVEL=<log_level>
STABLE_WAIT_SECONDS=<integer>
RESCAN_INTERVAL_SECONDS=<integer>

# Container timezone
TZ=UTC
```

Create the file if it doesn't exist yet and fill the required variables. Build the container if that has not been done yet. Next, one can start the container:

```bash
cd alliander_robotics/rclone
docker container build --no-cache rclone_filesync
docker compose up -d
```

To inspect the logs, run the following command in a terminal:

```bash
docker compose logs -f rclone_filesync
```
