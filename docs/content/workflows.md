<!--
SPDX-FileCopyrightText: Alliander N. V.

SPDX-License-Identifier: Apache-2.0
-->

# Workflows

We make use of different Github workflows to automatically validate the code in this repository.

## Linting

The Linting workflow contains the following checks:

- **ruff**:\
Lint all Python files according to the rules in `pyproject.toml`. See the full list of [Ruff rules](https://docs.astral.sh/ruff/rules/#error-e) for details.

- **pydoclint**\:
Checks the docstring of the .py files using the rules specified in *pyproject.toml*. These checks might be implemented in Ruff in the [future](https://github.com/astral-sh/ruff/issues/12434), but for now we use pydoclint for the additional checks not available in Ruff.

- **clang-format**:\
Checks the formatting of the .cpp, .h and .hpp files in this repository.

- **cppformat**:\
Static code checker for .cpp files in this repository.

- **reuse**:\
Checks all files in this repository on usage of copyright terms.

- **Ty**:\
Runs static type checks on our Python code using [Ty](https://github.com/astral-sh/ty).  

- **doxygen**:\
Runs code documentation checks for .cpp, .hpp, and .h files, using the rules specified in *doxyfile.lint*. In the future, other filetypes may be added as well.

### Local Development

You can run these checks locally before committing by running `uv run start.py --linting` which uses the [`pre-commit`](https://pre-commit.com/) framework.

This will help you catch issues early and avoid failing commits in CI.

## Documentation

The Documentation workflow automatically builds HTML pages form the files in the docs folder of this repository using Sphinx. Next, the HTML pages are automatically pushed to the Github Pages of this repository.

## Docker

The Docker workflows in this repository handle multi-architecture builds, selective component deployment, and cleanup. They support `amd64` and `arm64` architectures and are split across three workflows: `main.yml`, `pr.yml`, and `pr-closed.yml`.

1. **Main Branch Workflow** (`main.yml`)
    - **Select Components**: Gathers all components.
    - **Build Base Images**: Builds `base` (Ubuntu) and `cuda` images for all architectures.
    - **Build Component Images**: Builds all Ubuntu- and CUDA-based components that depend on the updated base images.
    - **Linting**: Runs `alliander_tests` container with `--linting` to check code style.
    - **Testing**: Runs integration and end-to-end tests in `alliander_tests` container with `--pytest-no-nvidia` (GPU tests skipped). Full test coverage is run using `--mode all`.

2. **Pull Request Workflow** (`pr.yml`)
    - **Select Components**: Detects only the components affected by the PR relative to the main branch.
    - **Conditional Builds**:
      - Builds `base` and `cuda` only if `REBUILD_CORE` is true.
      - Builds Ubuntu and CUDA component images only if `REBUILD_UBUNTU_IMAGES` or `REBUILD_CUDA_IMAGES` are `true`.
      - Images are tagged with the branch name to allow traceability, keep images from different PRs separate, and ensure that the main branch always uses stable, working images rather than potentially unstable PR builds.
    - **Linting**: Runs `alliander_tests` container with `--linting` to check code style.
    - **Testing**: Runs tests only for components affected by the PR, skipping GPU tests with `--pytest-no-nvidia`.

3. **Pull Request Closed Workflow** (`pr-closed.yml`)
    - **Automatic Cleanup**:
      - Triggered when a pull request is closed (merged or discarded).
      - Removes Docker images and tags associated with the PR branch on Docker Hub.
      - Uses a GitHub Action to authenticate to Docker Hub and a Python script (`github.py`) to delete branch-specific tags.

