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
        pytest.param(
            {"bitrise": {"workflows": ["foo"]}}, {}, Exception, id="missing app"
        ),
        pytest.param(
            {"bitrise": {"app": "foo"}}, {}, Exception, id="missing workflows"
        ),
        pytest.param(
            {"bitrise": {"app": "foo", "workflows": {"err": "nope"}}},
            {},
            Exception,
            id="wrong workflows format",
        ),
        pytest.param(
            {"bitrise": {"app": "foo", "workflows": [{"nope": ["wut"]}]}},
            {},
            Exception,
            id="wrong workflows format2",
        ),
        pytest.param(
            {"bitrise": {"app": "foo", "workflows": [{"foo": {"bar": ["oops"]}}]}},
            {},
            Exception,
            id="wrong workflows format3",
        ),
        pytest.param(
            {"bitrise": {"app": "some-app", "workflows": ["bar", "baz"]}},
            {},
            {
                "payload": {
                    "global_params": {
                        "branch": "default",
                        "branch_repo_owner": "http://example.com/head/repo",
                        "commit_hash": "abcdef",
                    },
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
            {
                "tasks_for": "github-pull-request",
                "commit_message": "This is a commit",
                "pull_request_number": "123",
            },
            {
                "payload": {
                    "global_params": {
                        "branch": "default",
                        "branch_dest": "123456",
                        "branch_dest_repo_owner": "http://example.com/base/repo",
                        "branch_repo_owner": "http://example.com/head/repo",
                        "commit_hash": "abcdef",
                        "pull_request_author": "some-owner",
                        "commit_message": "This is a commit",
                        "pull_request_id": "123",
                    },
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
                "commit_message": "This is a commit",
                "pull_request_number": "123",
            },
            {
                "payload": {
                    "global_params": {
                        "branch_repo_owner": "http://example.com/head/repo",
                        "commit_hash": "abcdef",
                        "pull_request_author": "some-owner",
                        "tag": "some-tag",
                        "commit_message": "This is a commit",
                        "pull_request_id": "123",
                    }
                },
                "scopes": ["foo:bitrise:app:some-app", "foo:bitrise:workflow:bar"],
                "tags": {"worker-implementation": "scriptworker"},
            },
            id="opposite params",  # this test helps hit other half of if statements
        ),
        pytest.param(
            {"bitrise": {"app": "some-app", "workflows": ["bar"]}},
            {
                "base_ref": "refs/heads/foo",
                "base_repository": "",
                "head_ref": "refs/heads/bar",
                "head_tag": "refs/tags/some-tag",
                "tasks_for": "github-pull-request",
                "commit_message": "This is a commit",
                "pull_request_number": "123",
            },
            {
                "payload": {
                    "global_params": {
                        "branch": "bar",
                        "branch_dest": "foo",
                        "branch_repo_owner": "http://example.com/head/repo",
                        "commit_hash": "abcdef",
                        "pull_request_author": "some-owner",
                        "tag": "some-tag",
                        "commit_message": "This is a commit",
                        "pull_request_id": "123",
                    }
                },
                "scopes": ["foo:bitrise:app:some-app", "foo:bitrise:workflow:bar"],
                "tags": {"worker-implementation": "scriptworker"},
            },
            id="normalize refs",
        ),
        pytest.param(
            {"bitrise": {"app": "some-app", "workflows": ["bar"]}},
            {
                "base_ref": "refs/tags/foo",
                "base_repository": "",
                "head_ref": "refs/tags/bar",
                "head_tag": "refs/heads/some-tag",
                "tasks_for": "github-pull-request",
                "commit_message": "This is a commit",
                "pull_request_number": "123",
            },
            {
                "payload": {
                    "global_params": {
                        "branch_repo_owner": "http://example.com/head/repo",
                        "commit_hash": "abcdef",
                        "pull_request_author": "some-owner",
                        "commit_message": "This is a commit",
                        "pull_request_id": "123",
                    }
                },
                "scopes": ["foo:bitrise:app:some-app", "foo:bitrise:workflow:bar"],
                "tags": {"worker-implementation": "scriptworker"},
            },
            id="normalize refs wrong type",
        ),
        pytest.param(
            {
                "bitrise": {
                    "app": "some-app",
                    "workflows": [
                        "foo",
                        {
                            "bar": {
                                "FOO": "bar",
                                "PATH": {"artifact-reference": "<build/target.zip>"},
                            }
                        },
                    ],
                }
            },
            {},
            {
                "payload": {
                    "global_params": {
                        "branch": "default",
                        "branch_repo_owner": "http://example.com/head/repo",
                        "commit_hash": "abcdef",
                    },
                    "workflow_params": {
                        "bar": {
                            "environments": [
                                {"mapped_to": "FOO", "value": "bar"},
                                {
                                    "mapped_to": "PATH",
                                    "value": {
                                        "artifact-reference": "<build/target.zip>"
                                    },
                                },
                            ]
                        }
                    },
                },
                "scopes": [
                    "foo:bitrise:app:some-app",
                    "foo:bitrise:workflow:foo",
                    "foo:bitrise:workflow:bar",
                ],
                "tags": {"worker-implementation": "scriptworker"},
            },
            id="environments",
        ),
        pytest.param(
            {
                "bitrise": {
                    "artifact_prefix": "public",
                    "app": "some-app",
                    "workflows": ["bar"],
                }
            },
            {},
            {
                "payload": {
                    "artifact_prefix": "public",
                    "global_params": {
                        "branch": "default",
                        "branch_repo_owner": "http://example.com/head/repo",
                        "commit_hash": "abcdef",
                    },
                },
                "scopes": [
                    "foo:bitrise:app:some-app",
                    "foo:bitrise:workflow:bar",
                ],
                "tags": {"worker-implementation": "scriptworker"},
            },
            id="artifact prefix",
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
