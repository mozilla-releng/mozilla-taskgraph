import sys
from itertools import count

import pytest
import taskcluster_urls as liburl
from taskgraph.util.taskcluster import get_artifact_url

from mozilla_taskgraph.actions import enable_action

from ..conftest import make_graph, make_task


@pytest.fixture(scope="session", autouse=True)
def enable():
    enable_action("release-promotion")


@pytest.fixture(scope="session", autouse=True)
def mock_version(session_mocker):
    m = session_mocker.patch("mozilla_taskgraph.version.default_parser")
    m.return_value = "1.0.0"


@pytest.fixture
def setup(responses, parameters):
    tc_url = liburl.test_root_url()

    def inner(previous_graphs=None):
        if not previous_graphs:
            decision_id = "d0"
            previous_graphs = {
                decision_id: make_graph(
                    make_task(
                        "a",
                    ),
                    make_task(
                        "b",
                    ),
                )
            }
            # An extra call is made to find the decision id if not explicitly
            # passed in.
            responses.add(
                method="GET",
                url=f"{tc_url}/api/index/v1/task/test.v2.some-project.pushlog-id.1.decision",
                json={"taskId": decision_id},
            )

        # Only the parameters from the first previous graph is downloaded.
        responses.add(
            method="GET",
            url=get_artifact_url(
                list(previous_graphs.keys())[0], "public/parameters.yml"
            ),
            json=parameters,
        )

        tid = count(0)
        for decision_id, full_task_graph in previous_graphs.items():
            responses.add(
                method="GET",
                url=get_artifact_url(decision_id, "public/full-task-graph.json"),
                json=full_task_graph.to_json(),
            )
            label_to_taskid = {label: int(next(tid)) for label in full_task_graph.tasks}
            responses.add(
                method="GET",
                url=get_artifact_url(decision_id, "public/label-to-taskid.json"),
                json=label_to_taskid,
            )

    return inner


def assert_call(datadir, mock, expected_params):
    mock.assert_called_once()
    args, kwargs = mock.call_args
    assert args == ({"root": str(datadir / "taskcluster")},)
    assert len(kwargs) == 1
    assert kwargs["parameters"] == expected_params


def test_release_promotion(parameters, setup, run_action, datadir):
    setup()
    expected_params = parameters.copy()
    expected_params.update(
        {
            "build_number": 2,
            "do_not_optimize": [],
            "existing_tasks": {"a": 0, "b": 1},
            "optimize_target_tasks": True,
            "shipping_phase": "promote",
            "target_tasks_method": "target_promote",
            "tasks_for": "action",
            "version": "1.0.0",
        }
    )

    input = {"build_number": "2", "release_promotion_flavor": "promote", "version": ""}
    mock = run_action("release-promotion", parameters, input)
    assert_call(datadir, mock, expected_params)


def test_release_promotion_custom_version_parser(
    parameters, setup, run_action, datadir, make_graph_config
):
    setup()
    expected_params = parameters.copy()
    expected_params.update(
        {
            "build_number": 2,
            "do_not_optimize": [],
            "existing_tasks": {"a": 0, "b": 1},
            "optimize_target_tasks": True,
            "shipping_phase": "promote",
            "target_tasks_method": "target_promote",
            "tasks_for": "action",
            "version": "99",
        }
    )

    graph_config = make_graph_config(
        extra_config={"version-parser": "testver:fake_version"}
    )
    input = {"build_number": "2", "release_promotion_flavor": "promote", "version": ""}
    try:
        sys.path.insert(0, str(datadir))
        mock = run_action("release-promotion", parameters, input, graph_config)
    finally:
        sys.path.pop(0)
    assert_call(datadir, mock, expected_params)


def test_release_promotion_combine_previous_graphs(
    parameters, setup, run_action, datadir
):
    """Test that more than one 'previous_graph_ids' can be passed and their
    full_task_graphs are combined."""
    previous_graphs = {
        "d0": make_graph(
            make_task(
                "a",
            ),
            make_task(
                "b",
            ),
        ),
        "d1": make_graph(
            make_task(
                "b",
            ),
            make_task(
                "c",
            ),
        ),
    }
    setup(previous_graphs)
    expected_params = parameters.copy()
    expected_params.update(
        {
            "do_not_optimize": [],
            "existing_tasks": {"a": 0, "b": 2, "c": 3},
            "optimize_target_tasks": True,
            "shipping_phase": "ship",
            "target_tasks_method": "target_ship",
            "tasks_for": "action",
            "version": "1.0.0",
        }
    )

    input = {
        "build_number": "1",
        "release_promotion_flavor": "ship",
        "previous_graph_ids": ["d0", "d1"],
        "version": "",
    }
    mock = run_action("release-promotion", parameters, input)
    assert_call(datadir, mock, expected_params)


def test_release_promotion_rebuild_kinds(parameters, setup, run_action, datadir):
    previous_graphs = {
        "d0": make_graph(
            make_task(
                "a",
            ),
            make_task("b", kind="rebuild", attributes={"kind": "rebuild"}),
        ),
    }
    setup(previous_graphs)
    expected_params = parameters.copy()
    expected_params.update(
        {
            "do_not_optimize": [],
            "existing_tasks": {"a": 0},
            "optimize_target_tasks": True,
            "shipping_phase": "promote",
            "target_tasks_method": "target_promote",
            "tasks_for": "action",
            "version": "1.0.0",
        }
    )

    input = {
        "build_number": "1",
        "release_promotion_flavor": "promote",
        "rebuild_kinds": ["rebuild"],
        "previous_graph_ids": ["d0"],
        "version": "",
    }
    mock = run_action("release-promotion", parameters, input)
    assert_call(datadir, mock, expected_params)


def test_release_promotion_version(parameters, setup, run_action, datadir):
    setup()
    expected_params = parameters.copy()
    expected_params.update(
        {
            "build_number": 2,
            "do_not_optimize": [],
            "existing_tasks": {"a": 0, "b": 1},
            "optimize_target_tasks": True,
            "shipping_phase": "promote",
            "target_tasks_method": "target_promote",
            "tasks_for": "action",
            "version": "2.0",
        }
    )

    input = {
        "build_number": "2",
        "release_promotion_flavor": "promote",
        "version": "2.0",
    }
    mock = run_action("release-promotion", parameters, input)
    assert_call(datadir, mock, expected_params)
