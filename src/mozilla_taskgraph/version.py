import os

from taskgraph.util.vcs import get_repository

here = os.path.abspath(os.path.dirname(__file__))


def default_parser(params):
    repo_root = get_repository(here).path

    with open(os.path.join(repo_root, "version.txt")) as f:
        return f.read().strip()
