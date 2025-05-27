from pathlib import Path

import pytest
import taskcluster_urls as liburl
from responses import RequestsMock
from taskgraph import create
from taskgraph.actions import trigger_action_callback
from taskgraph.config import load_graph_config
from taskgraph.graph import Graph
from taskgraph.task import Task
from taskgraph.taskgraph import TaskGraph
from taskgraph.transforms.base import GraphConfig, TransformConfig
from taskgraph.util import taskcluster as tc_util

from mozilla_taskgraph.actions import release_promotion

here = Path(__file__).parent


@pytest.fixture(scope="session", autouse=True)
def set_taskcluster_url(session_mocker):
    session_mocker.patch.dict(
        "os.environ", {"TASKCLUSTER_ROOT_URL": liburl.test_root_url()}
    )


@pytest.fixture
def responses():
    with RequestsMock() as rsps:
        yield rsps


@pytest.fixture(scope="session")
def datadir():
    return here / "data"


@pytest.fixture(scope="session")
def repo_root():
    return here.parent


@pytest.fixture(scope="session")
def make_graph_config(datadir):
    def inner(root_dir=None, extra_config=None):
        root_dir = root_dir or str(datadir / "taskcluster")
        config = load_graph_config(root_dir)._config.copy()
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
            "app_version": "99.0",
            "base_ref": "123456",
            "base_repository": "http://example.com/base/repo",
            "build_date": 0,
            "build_number": 1,
            "enable_always_target": True,
            "head_repository": "http://example.com/head/repo",
            "head_rev": "abcdef",
            "head_ref": "default",
            "head_tag": "",
            "level": "1",
            "moz_build_date": 0,
            "next_version": "100.0",
            "owner": "some-owner",
            "project": "some-project",
            "pushlog_id": 1,
            "repository_type": "hg",
            "target_tasks_method": "test_method",
            "tasks_for": "hg-push",
            "try_mode": None,
            "version": "99.0",
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


@pytest.fixture
def run_action(mocker, monkeypatch, graph_config):
    # Monkeypatch these here so they get restored to their original values.
    # Otherwise, `trigger_action_callback` will leave them set to `True` and
    # cause failures in other tests.
    monkeypatch.setattr(create, "testing", True)
    monkeypatch.setattr(tc_util, "testing", True)
    root_dir = graph_config.root_dir

    def inner(name, parameters, input, graph_config=None):
        m = mocker.patch.object(release_promotion, "taskgraph_decision")
        m.return_value = lambda *args, **kwargs: (args, kwargs)

        gc_mock = None
        if graph_config:
            gc_mock = mocker.patch("taskgraph.actions.registry.load_graph_config")
            gc_mock.return_value = graph_config

        trigger_action_callback(
            task_group_id="group-id",
            task_id=None,
            input=input,
            callback=name,
            parameters=parameters,
            root=root_dir,
            test=True,
        )

        if gc_mock:
            gc_mock.reset()

        return m

    return inner


def make_task(
    label,
    kind="test",
    optimization=None,
    task_def=None,
    task_id=None,
    dependencies=None,
    if_dependencies=None,
    attributes=None,
):
    task_def = task_def or {
        "sample": "task-def",
        "deadline": {"relative-datestamp": "1 hour"},
    }
    task = Task(
        attributes=attributes or {},
        if_dependencies=if_dependencies or [],
        kind=kind,
        label=label,
        task=task_def,
    )
    task.optimization = optimization
    task.task_id = task_id
    if dependencies is not None:
        task.task["dependencies"] = sorted(dependencies)
    return task


def make_graph(*tasks_and_edges, **kwargs):
    tasks = {t.label: t for t in tasks_and_edges if isinstance(t, Task)}
    edges = {e for e in tasks_and_edges if not isinstance(e, Task)}
    tg = TaskGraph(tasks, Graph(set(tasks), edges))

    if kwargs.get("deps", True):
        # set dependencies based on edges
        for l, r, name in tg.graph.edges:
            tg.tasks[l].dependencies[name] = r

    return tg
