from pathlib import Path

import pytest
from taskgraph.transforms.base import GraphConfig, TransformConfig

here = Path(__file__).parent


@pytest.fixture(scope="session")
def datadir():
    return here / "data"


@pytest.fixture(scope="session")
def make_graph_config(datadir):
    def inner(root_dir=None, extra_config=None):
        root_dir = root_dir or str(datadir / "taskcluster" / "ci")
        config = {
            "trust-domain": "test-domain",
            "taskgraph": {
                "repositories": {
                    "ci": {"name": "Mozilla Taskgraph"},
                }
            },
            "workers": {
                "aliases": {
                    "b-linux": {
                        "provisioner": "taskgraph-b",
                        "implementation": "generic-worker",
                        "os": "linux",
                        "worker-type": "linux",
                    },
                    "t-linux": {
                        "provisioner": "taskgraph-t",
                        "implementation": "docker-worker",
                        "os": "linux",
                        "worker-type": "linux",
                    },
                }
            },
            "task-priority": "low",
            "treeherder": {"group-names": {"T": "tests"}},
            "index": {
                "products": [
                    "fake",
                ],
            },
        }
        if extra_config:
            config.update(extra_config)

        graph_config = GraphConfig(config, root_dir)
        graph_config.__dict__["register"] = lambda: None
        return graph_config

    return inner


@pytest.fixture(scope="session")
def graph_config(make_graph_config):
    return make_graph_config()


class FakeParameters(dict):
    strict = True

    def is_try(self):
        return False

    def file_url(self, path, pretty=False):
        return path


@pytest.fixture
def parameters():
    return FakeParameters(
        {
            "base_repository": "http://hg.example.com",
            "build_date": 0,
            "build_number": 1,
            "enable_always_target": True,
            "head_repository": "http://hg.example.com",
            "head_rev": "abcdef",
            "head_ref": "default",
            "level": "1",
            "moz_build_date": 0,
            "next_version": "1.0.1",
            "owner": "some-owner",
            "project": "some-project",
            "pushlog_id": 1,
            "repository_type": "hg",
            "target_tasks_method": "test_method",
            "tasks_for": "hg-push",
            "try_mode": None,
            "version": "1.0.0",
        }
    )


@pytest.fixture
def make_transform_config(parameters, graph_config):
    def inner(
        kind_config=None, kind_dependencies_tasks=None, graph_cfg=None, params=None
    ):
        kind_config = kind_config or {}
        kind_dependencies_tasks = kind_dependencies_tasks or {}
        graph_cfg = graph_cfg or graph_config
        params = params or parameters
        return TransformConfig(
            "test",
            str(here),
            kind_config,
            params,
            kind_dependencies_tasks,
            graph_cfg,
            write_artifacts=False,
        )

    return inner


@pytest.fixture
def run_transform(make_transform_config):
    def inner(func, tasks, config=None):
        if not isinstance(tasks, list):
            tasks = [tasks]

        if not config:
            config = make_transform_config()
        return list(func(config, tasks))

    return inner
