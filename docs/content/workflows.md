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
Checks the format of the .cpp, .h and .hpp files in this repository.

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

The Docker workflow is the most extensive workflow of this repository. This workflow can also be tested locally using [Act](https://github.com/nektos/act) with the command:

```bash
act --rm -W .github/workflows/docker.yml
```

The workflow contains the following steps, both for the `amd64` and `arm64` architectures:

1. Check where there are changes compared to last commit for each of the `rcdt_<package>` folders.
2. If `rcdt_core` is changed, a new `base` image is built.
3. For all other packages with changes that are based on `rcdt/robotics:base`, new images are built.
4. For all built images based on `rcdt/robotics:base`, a manifest is created. This combines the `amd64` and `arm64` images into one multi-arch image.
5. If `rcdt_core` is changed, a new `cuda` image is built.
6. For all other packages with changes that are based on `rcdt/robotics:cuda`, new images are built.
7. For all built images based on `rcdt/robotics:cuda`, a manifest is created.
8. The `rcdt_tests` container is run with the `--linting` flag, which runs the *Linting* as outlined above.
9. The `rcdt_tests` container is run with the `--pytest-no-nvidia` flag, which runs integration and end-to-end tests. Any tests requiring a GPU are not run, as the currently available GitHub runners do not have a GPU.
