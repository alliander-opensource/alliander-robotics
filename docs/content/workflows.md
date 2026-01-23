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

## Docker and Workspace

The Docker and Workspace workflow is the most extensive workflow of this repository. This workflow can also be tested locally using [Act](https://github.com/nektos/act) with the command:

```bash
act --rm -W .github/workflows/linting.yml
```

The workflow contains the following steps:

- Check wether the workflow is executed on Github or locally.
- Define the git branch in use.
- Check wether files are changed in the *dockerfiles* directory compared to the main branch.
  - If changes are made, a new docker image gets build and pushed to the Docker Hub.
- The correct docker image gets pulled and used to build the ros-workspace and run the tests using Pytest.
