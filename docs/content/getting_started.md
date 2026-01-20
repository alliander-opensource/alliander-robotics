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

This project uses [uv](https://docs.astral.sh/uv/) to manage Python packages, and should be installed locally on your computer. To install everything needed for the ROS packages, the following command should be added to each Dockerfile (optionally with additional flags):

```bash
RUN uv sync
```

This will install all the Python dependencies in the `.venv` directory in the root of the repository. The `.venv` directory is automatically created if it does not exist yet. You can now use these dependencies in your ROS packages. To learn more about all the available features of uv, please refer to the [uv feature documentation](https://docs.astral.sh/uv/getting-started/features/).


## Build ROS packages

The ROS packages automatically build and sourced within each separate container. Each Dockerfile within a ROS package contains the following command:

```bash
RUN /rcdt/colcon_build.sh
```

As the command already suggests, to build the ROS packages, we use colcon. We build with the `--symlink-install` flag. This will make symlinks between the build files and source files. Changes to Python, YAML or Launch files are now automatically applied without the need of rebuilding. 

:::{note}
With the `--symlink-install` flag, only changes to files that did exist while building are automatically applied. If you make changes to the file structure (rename or create files), you still need to build again.
:::

:::{note}
In case you want to work within the started containers and want to work with your own aliases, you can add an alias to your personal bashrc file in the root of the repository (`.personal.bashrc`). You could for example add:

```bash
alias cb="cd /home/rcdt/rcdt_robotics/ros2_ws; uv run colcon build --symlink-install; source install/setup.bash"
```

From now on, when you open a new terminal, this alias is available and you can simply build and source using the `cb` command.
:::


## Run a configuration

Before running a specific configuration, make sure to have build the docker images locally by executing the following command:

```bash
uv run image_manager.py --build
```

Or, when you haven't made changes yet to the code, you can also pull the existing docker images from our [Docker Hub](https://hub.docker.com/r/rcdt/robotics) by using the `--pull` flag. If this is the first time, it can take quite some time to pull the image.

```bash
uv run image_manager.py --pull
```

In both cases it is possible to execute the task for a selected list of packages by adding the `--components` flag to the command.

:::{note}
The image that is pulled is automatically determined based on your current local branch. If the main branch is selected, it will use `rcdt/robotics:latest`. If you are on a branch that contains changes in the Docker files and a pull request is made, a corresponding Docker Image is automatically build by Github and pushed to Docker Hub. The run script will now use this new image when available.
:::

To automatically run a configuration, simply execute the following command in the root of the repository:

```bash
uv run start.py [-h] [--pytest ...] [--pytest-no-nvidia ...] [--linting]
                [--documentation] [-w] [-v] [-d] [-u]
                [configuration]
```

Note that the system won't start if no configuration is provided. The possible launch arguments can be found in the `predefined_configurations.py` file, the name of each configuration being noted above each function in `@register_configuration(...)`. Example execution command:

```bash
uv run start.py panther
```

The packages belonging to the specified configuration are automatically launched in their own docker containers via a command provided to the `docker-compose.yml` files. Depending on what configuration is provided to `start.py`, the desired `docker-compose.yml` files are combined and written to `compose.yml`, which will be placed in the root directory of the repository. 

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

When connected with the Panther network, communication with its ip-addresses in the 10.15.20.0/24 range should be allowed:

```bash
sudo ufw allow to 10.15.20.0/24
sudo ufw allow from 10.15.20.0/24
```
