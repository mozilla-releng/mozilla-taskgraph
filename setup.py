import os
from distutils.util import convert_path

from setuptools import find_packages, setup

project_dir = os.path.abspath(os.path.dirname(__file__))

version_file = convert_path("version.txt")
with open(version_file) as fh:
    version = fh.read().strip()

with open(os.path.join(project_dir, "requirements/base.in")) as fp:
    requirements = fp.read().splitlines()

with open(os.path.join(project_dir, "README.md")) as fh:
    long_description = fh.read()

setup(
    name="mozilla-taskgraph",
    version=version,
    description="Mozilla-specific transforms and utilities for Taskgraph",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/mozilla-releng/mozilla-taskgraph",
    packages=find_packages("src"),
    package_dir={"": "src"},
    install_requires=requirements,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development",
    ],
)
