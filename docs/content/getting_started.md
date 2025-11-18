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

## Run the container

To run a container from our Docker image, simply execute the run command in the root of the repository:

```bash
. run
```

This will pull an image from our [Docker Hub](https://hub.docker.com/r/rcdt/robotics). If this is the first time, it can take quite some time to pull the image. When pulling is finished, the image is started which can be seen by the user-name changing to white in the terminal. You can now execute commands inside the docker container.

After starting, the terminal is located in the home directory: `/home/rcdt`. The repository you you cloned is [*mounted*](https://docs.docker.com/engine/storage/bind-mounts/) and can be found at `/home/rcdt/rcdt_robotics`. Got to this directory by executing:

```bash
cd rcdt_robotics
```

:::{note}
The image that is pulled is automatically determined based on your current local branch. If the main branch is selected, it will use `rcdt/robotics:latest`. If you are on a branch that contains changes in the Docker files and a pull request is made, a corresponding Docker Image is automatically build by Github and pushed to Docker Hub. The run script will now use this new image when available.
:::

## Install Python dependencies with uv

This project uses [uv](https://docs.astral.sh/uv/) to manage Python packages. To install everything needed for the ROS packages, run the following command from the `rcdt_robotics` repository root:

```bash
uv sync
```

This will install all the Python dependencies in the `.venv` directory in the root of the repository. The `.venv` directory is automatically created if it does not exist yet. You can now use these dependencies in your ROS packages. To learn more about all the available features of uv, please refer to the [uv feature documentation](https://docs.astral.sh/uv/getting-started/features/).

## Build ROS packages

The ROS packages are located in the `ros2_ws/src` directory inside the repository. It is recommend to build the ROS package inside the `ros2_ws` directory. First go to this directory:

```bash
cd ros2_ws
```

To build the ROS packages, we use colcon. We recommend to build with the `--symlink-install` flag. This will make symlinks between the build files and source files. Changes to Python, YAML or Launch files are now automatically applied without the need of rebuilding. Run the command to build the ROS packages:

```bash
uv run colcon build --symlink-install
```

After building, you need to source the files you build:

```bash
source /home/rcdt/rcdt_robotics/ros2_ws/install/setup.bash
```

:::{note}
With the `--symlink-install` flag, only changes to files that did exist while building are automatically applied. If you make changes to the file structure (rename or create files), you still need to build again.
:::

:::{note}
To simplify the process of building, you can add an alias to your personal bashrc file in the root of the repository (`.personal.bashrc`). You could for example add:

```bash
alias cb="cd /home/rcdt/rcdt_robotics/ros2_ws; uv run colcon build --symlink-install; source install/setup.bash"
```

From now on, when you open a new terminal, this alias is available and you can simply build and source using the `cb` command.
:::

## Launch

You can now launch our system using:

```bash
ros2 launch rcdt_launch bringup.launch.py
```

Note that the system won't start if no configuration is provided. The possible launch arguments can be acquired by adding the `-s` flag. More information about launching the system and selecting a configuration can be found on the [](system) page.

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
