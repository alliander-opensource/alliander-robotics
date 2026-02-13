<!--
SPDX-FileCopyrightText: Alliander N. V.

SPDX-License-Identifier: Apache-2.0
-->

# Writing Documentation

## File Structure

This documentation is generated using [Sphinx](https://www.sphinx-doc.org). The source files are located in `alliander-robotics/docs`. If changes are made in this directory and merged to the main branch, a GitHub workflow automatically generates HTML from the source file and deploys these at the documentation [page](https://alliander-opensource.github.io/alliander-robotics/).

Although *.rst* (reStructuredText) is the default format for Sphinx documentation, we only use *index.rst* to define the structure of our documentation. All other documentation files are *.md* (Markdown) because of the simpler syntax.  

The *README.md* file is the "home" page of our documentation page and our GitHub repository. All other documentation can be found in the `content` directory.

## Adding Documentation

Documentation can be added by creating a new *.md* file in the content directory. After creating the file, it also needs to be added to *index.rst*. To check your changes locally, you can use the *sphinx-autobuild* tool. Run the following command to start automatic building using Sphinx:

```bash
uv run start.py --documentation
```

You can now view a live version, of which the URL can be found in the terminal. Every time you change a file and save, the tool builds the new HTML files and refreshes the page.
