import inspect
from pprint import pprint

import pytest
from taskgraph.transforms.task import payload_builders
from taskgraph.util.schema import validate_schema

from mozilla_taskgraph import worker_types


@pytest.mark.parametrize(
    "worker,extra_params,expected",
    (
        pytest.param({}, {}, Exception, id="missing bitrise"),
        pytest.param({"bitrise": {"workflows": []}}, {}, Exception, id="missing app"),
        pytest.param(
            {"bitrise": {"app": "foo"}}, {}, Exception, id="missing workflows"
        ),
        pytest.param(
            {"bitrise": {"app": "some-app", "workflows": ["bar", "baz"]}},
            {},
            {
                "payload": {
                    "branch": "default",
                    "branch_repo_owner": "http://example.com/head/repo",
                    "commit_hash": "abcdef",
                },
                "scopes": [
                    "foo:bitrise:app:some-app",
                    "foo:bitrise:workflow:bar",
                    "foo:bitrise:workflow:baz",
                ],
                "tags": {"worker-implementation": "scriptworker"},
            },
            id="default params",
        ),
        pytest.param(
            {"bitrise": {"app": "some-app", "workflows": ["bar"]}},
            {"tasks_for": "github-pull-request"},
            {
                "payload": {
                    "branch": "default",
                    "branch_dest": "123456",
                    "branch_dest_repo_owner": "http://example.com/base/repo",
                    "branch_repo_owner": "http://example.com/head/repo",
                    "commit_hash": "abcdef",
                    "pull_request_author": "some-owner",
                },
                "scopes": ["foo:bitrise:app:some-app", "foo:bitrise:workflow:bar"],
                "tags": {"worker-implementation": "scriptworker"},
            },
            id="pull request",
        ),
        pytest.param(
            {"bitrise": {"app": "some-app", "workflows": ["bar"]}},
            {
                "base_ref": "",
                "base_repository": "",
                "head_ref": "",
                "head_tag": "some-tag",
                "tasks_for": "github-pull-request",
            },
            {
                "payload": {
                    "branch_repo_owner": "http://example.com/head/repo",
                    "commit_hash": "abcdef",
                    "pull_request_author": "some-owner",
                    "tag": "some-tag",
                },
                "scopes": ["foo:bitrise:app:some-app", "foo:bitrise:workflow:bar"],
                "tags": {"worker-implementation": "scriptworker"},
            },
            id="opposite params",  # this test helps hit other half of if statements
        ),
    ),
)
def test_build_bitrise_payload(
    make_graph_config, make_transform_config, parameters, worker, extra_params, expected
):
    schema = payload_builders["scriptworker-bitrise"].schema

    graph_config = make_graph_config(
        extra_config={"scriptworker": {"scope-prefix": "foo"}}
    )
    parameters.update(extra_params)
    config = make_transform_config(params=parameters, graph_cfg=graph_config)

    worker.setdefault("implementation", "scriptworker-bitrise")
    task = {"worker": worker}
    task_def = {"tags": {}}

    if inspect.isclass(expected) and issubclass(expected, Exception):
        with pytest.raises(expected):
            validate_schema(schema, worker, "schema error")
            worker_types.build_bitrise_payload(config, task, task_def)
    else:
        validate_schema(schema, worker, "schema error")
        worker_types.build_bitrise_payload(config, task, task_def)
        print("Dumping result:")
        pprint(task_def, indent=2)
        assert task_def == expected


def test_build_shipit_payload():
    task = {"worker": {"release-name": "foo"}}
    task_def = {"tags": {}}
    worker_types.build_shipit_payload(None, task, task_def)
    assert task_def == {
        "payload": {"release_name": "foo"},
        "tags": {"worker-implementation": "scriptworker"},
    }
