import os
from distutils.util import convert_path

from setuptools import find_packages, setup

project_dir = os.path.abspath(os.path.dirname(__file__))

namespace = {}
version_file = convert_path("src/mozilla_taskgraph/__init__.py")
with open(version_file) as fh:
    exec(fh.read(), namespace)

with open(os.path.join(project_dir, "requirements/base.in")) as fp:
    requirements = fp.read().splitlines()

setup(
    name="mozilla-taskgraph",
    version=namespace["__version__"],
    description="Mozilla-specific transforms and utilities for Taskgraph",
    url="https://github.com/mozilla-releng/mozilla-taskgraph",
    packages=find_packages("src"),
    package_dir={"": "src"},
    install_requires=requirements,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development",
    ],
)
