<!--
SPDX-FileCopyrightText: Alliander N. V.

SPDX-License-Identifier: Apache-2.0
-->

# Getting Started

## Prerequisites

**Docker**\
We provide docker images to simplify the installation of all the software dependencies. To use these image, you need to install docker first. Please follow [these](docker) instructions to install docker.

**Git LFS**\
The repository uses git LFS for large files, in particular for 3D simulation assets. To clone these large files, you need to install git LFS. Please follow  [these](https://git-lfs.com/) instructions to install git LFS.

## Clone

To use this repository, first clone it. If you are a contributor with an SSH-key linked, clone via SSH:

```bash
git clone git@github.com:alliander-opensource/rcdt_robotics.git
```

If you only want to use the repository without contributing, you can clone via HTTP:

```bash
git clone https://github.com/alliander-opensource/rcdt_robotics.git
```

## Python dependencies installed with uv

This project uses [uv](https://docs.astral.sh/uv/) to manage Python packages, and [can be installed](https://docs.astral.sh/uv/getting-started/installation/) locally on your computer using a single command:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Next, you can sync our project dependencies in a virtual environment using:

```bash
uv sync
```

This will install all the Python dependencies in the `.venv` directory in the root of the repository. The `.venv` directory is automatically created if it does not exist yet. To learn more about all the available features of uv, please refer to the [uv feature documentation](https://docs.astral.sh/uv/getting-started/features/).

## Get the Docker images

This repository support different robot and sensor platforms, which are described in the [Platforms](platforms) section. We provide docker images for the different platforms and for dependencies like Gazebo, MoveIt and Nav2. One can build these containers using:

```bash
uv run image_manager.py --build
```

Or, when you haven't made changes yet to the code, you can also pull the existing docker images from our [Docker Hub](https://hub.docker.com/r/rcdt/robotics) by using the `--pull` flag. If this is the first time, it can take quite some time to pull the image.

```bash
uv run image_manager.py --pull
```

In both cases it is possible to execute the task for a selected list of packages by adding the `--components` flag to the command.

## Run a configuration

This repository support the use of many combinations of robots and sensors (called configurations), which are defined in `predefined_configurations.py` where the name of each configuration being noted above each function in `@register_configuration(...)`. To run a configuration, simply execute the following command in the root of the repository:

```bash
uv run start.py [-h] [--pytest ...] [--pytest-no-nvidia ...] [--linting]
                [--documentation] [-w] [-v] [-d] [-u]
                [configuration]
```

Note that the system won't start if no configuration is provided. Instead of launching a configuration, one can also run pytest, linting or the creation of our documentation using the associated flags. As an example, the configuration of just the Panther (without other platforms) can be launched as:

```bash
uv run start.py panther
```

This will first create a docker compose file (`compose.yml`) in the root of the repository. This compose file contains the different docker images required to start the selected configuration, whereafter the whole compose file can be started to run all the images as docker containers.

## Firewall

It is recommended to enable your firewall in Ubuntu:

```bash
sudo ufw enable
```

However, some connections need to be allowed for proper working. First of all, multicast protocol is used in ROS middleware. To allow this, the ip ranges of multicast (224.0.0.0/4) should be allowed:

```bash
sudo ufw allow to 224.0.0.0/4
sudo ufw allow from 224.0.0.0/4
```

When connected with the Lynx or Panther network, communication with its ip-addresses in the 10.15.20.0/24 range should be allowed:

```bash
sudo ufw allow to 10.15.20.0/24
sudo ufw allow from 10.15.20.0/24
```
