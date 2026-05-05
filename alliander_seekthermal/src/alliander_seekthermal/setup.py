# SPDX-FileCopyrightText: Alliander N. V.
#
# SPDX-License-Identifier: Apache-2.0
import os
from glob import glob

from setuptools import setup

package_name = "alliander_seekthermal"

setup(
    name=package_name,
    version="0.1.0",
    packages=[package_name],
    package_dir={"": "src_py"},
    data_files=[
        ("share/ament_index/resource_index/packages", [f"resource/{package_name}"]),
        (f"share/{package_name}", ["package.xml"]),
        (os.path.join("share", package_name, "launch"), glob("launch/*.launch.py")),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="Alliander Robotics",
    maintainer_email="your@email.com",
    description="ROS2 bridge node for the Seek Thermal G300 camera.",
    license="Apache 2.0",
    entry_points={
        "console_scripts": [
            f"{package_name} = {package_name}.alliander_seekthermal:main",
        ],
    },
)
