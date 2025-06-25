from itertools import count
from pprint import pprint
from unittest.mock import Mock

import pytest
from requests import HTTPError
from taskgraph.util.templates import merge

from mozilla_taskgraph.transforms.replicate import transforms as replicate_transforms

TC_ROOT_URL = "https://tc-tests.example.com"


def get_target_defs(*task_defs):
    default = {
        "task": {
            "extra": {
                "treeherder": "1",
            },
            "metadata": {"name": "task-b", "description": "description"},
            "payload": {
                "artifacts": {
                    "foo": {
                        "expires": "some datestamp",
                    },
                },
                "cache": {
                    "foo-level-3": "1",
                },
                "env": {
                    "SHOULD_NOT_BE_REMOVED": "1",
                    "SHOULD_BE_REMOVED_REV": "1",
                },
                "mounts": [
                    {
                        "cacheName": "cache-foo-level-3-name",
                    }
                ],
            },
            "provisionerId": "foo",
            "scopes": [
                "test:foo-level-3:scope",
            ],
        }
    }

    task_defs = task_defs or [{}]
    return [merge(default, task_def) for task_def in task_defs]


def get_expected(prefix, *task_defs):
    expected = []
    for task_def in task_defs:
        expected_task = merge(
            task_def,
            {
                "attributes": {
                    "replicate": prefix,
                },
                "dependencies": {},
                "description": "description",
                "label": f"{prefix}-{task_def['task']['metadata']['name']}",
                "task": {
                    "created": {"relative-datestamp": "0 seconds"},
                    "deadline": {"relative-datestamp": "1 day"},
                    "expires": {"relative-datestamp": "1 month"},
                    "metadata": {
                        "name": f"{prefix}-{task_def['task']['metadata']['name']}",
                    },
                    "payload": {
                        "artifacts": {
                            "foo": {
                                "expires": {
                                    "relative-datestamp": "1 month",
                                }
                            }
                        },
                        "cache": {
                            "test-level-1": "1",
                        },
                        "mounts": [{"cacheName": "cache-test-level-1-name"}],
                    },
                    "priority": "low",
                    "routes": [
                        "checks",
                    ],
                    "schedulerId": "test-level-1",
                    "scopes": [
                        "test:test-level-1:scope",
                    ],
                    "taskGroupId": "abc",
                },
            },
        )
        del expected_task["task"]["extra"]["treeherder"]
        del expected_task["task"]["payload"]["cache"]["foo-level-3"]
        del expected_task["task"]["payload"]["env"]["SHOULD_BE_REMOVED_REV"]
        del expected_task["task"]["payload"]["mounts"][0]
        del expected_task["task"]["scopes"][0]
        expected.append(expected_task)

    return expected


@pytest.fixture
def run_replicate(monkeypatch, run_transform):
    task_id = "abc"
    monkeypatch.setenv("TASK_ID", task_id)

    def inner(task):
        result = run_transform(replicate_transforms, task)
        pprint(result, indent=2)
        return result

    return inner


def test_missing_config(run_replicate):
    task = {}
    with pytest.raises(Exception):
        run_replicate(task)

    task["replicate"] = {}
    with pytest.raises(Exception):
        run_replicate(task)

    task["replicate"]["target"] = []
    assert run_replicate(task) == []


def test_requests_error(responses, run_replicate):
    task_id = "fwp41cUkRmara7CD6l2U3A"
    task = {
        "name": "foo",
        "replicate": {
            "target": [
                task_id,
            ]
        },
    }
    responses.get(
        f"{TC_ROOT_URL}/api/queue/v1/task/{task_id}/artifacts/public/task-graph.json",
        body=HTTPError("Artifact not found!", response=Mock(status_code=403)),
    )

    with pytest.raises(HTTPError):
        run_replicate(task)


def test_task_id(responses, run_replicate):
    task_id = "fwp41cUkRmara7CD6l2U3A"
    prefix = "kind-a"
    task = {
        "name": prefix,
        "replicate": {
            "target": [
                task_id,
            ]
        },
    }
    task_def = get_target_defs()[0]
    expected = get_expected(prefix, task_def)[0]

    responses.get(
        f"{TC_ROOT_URL}/api/queue/v1/task/{task_id}/artifacts/public/task-graph.json",
        body=HTTPError("Artifact not found!", response=Mock(status_code=404)),
    )
    responses.get(f"{TC_ROOT_URL}/api/queue/v1/task/{task_id}", json=task_def)

    result = run_replicate(task)
    assert len(result) == 1
    assert result[0] == expected


def test_index_path(responses, run_replicate):
    prefix = "kind-a"
    task_id = "def"
    index_path = "foo.bar"
    task = {
        "name": prefix,
        "replicate": {"target": [index_path]},
    }
    task_def = get_target_defs()[0]
    expected = get_expected(prefix, task_def)[0]

    responses.get(
        f"{TC_ROOT_URL}/api/index/v1/task/{index_path}", json={"taskId": task_id}
    )
    responses.get(
        f"{TC_ROOT_URL}/api/queue/v1/task/{task_id}/artifacts/public/task-graph.json",
        body=HTTPError("Artifact not found!", response=Mock(status_code=404)),
    )
    responses.get(f"{TC_ROOT_URL}/api/queue/v1/task/{index_path}", json=task_def)

    result = run_replicate(task)
    assert len(result) == 1
    assert result[0] == expected


def test_decision_task(responses, run_replicate):
    prefix = "kind-a"
    task_id = "fwp41cUkRmara7CD6l2U3A"
    task = {
        "name": prefix,
        "replicate": {
            "target": [
                task_id,
            ]
        },
    }
    task_defs = get_target_defs({}, {"task": {"metadata": {"name": "task-c"}}})
    expected = get_expected(prefix, *task_defs)

    counter = count()
    responses.get(
        f"{TC_ROOT_URL}/api/queue/v1/task/{task_id}/artifacts/public/task-graph.json",
        json={next(counter): task_def for task_def in task_defs},
    )
    result = run_replicate(task)
    assert result == expected


@pytest.mark.parametrize(
    "target_def",
    (
        pytest.param(
            {
                "attributes": {"foo": "bar"},
                "task": {"provisionerId": "releng-hardware"},
            },
            id="releng-hardware",
        ),
        pytest.param(
            {
                "attributes": {"foo": "bar"},
                "task": {"payload": {"features": {"runAsAdministrator": True}}},
            },
            id="runAsAdministrator",
        ),
        pytest.param(
            {},  # doesn't match 'include-attrs'
            id="include-attrs",
        ),
        pytest.param(
            {"attributes": {"foo": "bar", "baz": "1"}},
            id="exclude-attrs",
        ),
    ),
)
def test_filtered_out(responses, run_replicate, target_def):
    prefix = "kind-a"
    task_id = "fwp41cUkRmara7CD6l2U3A"
    task = {
        "name": prefix,
        "replicate": {
            "target": [
                task_id,
            ],
            "include-attrs": {
                "foo": "bar",
            },
            "exclude-attrs": {
                "baz": "1",
            },
        },
    }
    task_defs = get_target_defs(target_def)

    counter = count()
    responses.get(
        f"{TC_ROOT_URL}/api/queue/v1/task/{task_id}/artifacts/public/task-graph.json",
        json={next(counter): task_def for task_def in task_defs},
    )
    result = run_replicate(task)
    assert len(result) == 0
