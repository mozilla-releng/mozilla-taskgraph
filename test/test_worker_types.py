import inspect
from pprint import pprint
from typing import Dict, Optional, Tuple

import pytest
from taskgraph.transforms.task import payload_builders
from taskgraph.util.schema import validate_schema

import mozilla_taskgraph.worker_types  # noqa - trigger payload_builder registration


@pytest.fixture
def build_payload(make_graph_config, make_transform_config, parameters):
    graph_config = make_graph_config(
        extra_config={"scriptworker": {"scope-prefix": "foo"}}
    )

    def inner(
        name: str,
        worker: dict,
        extra_params: Optional[Dict] = None,
        raises: Optional[Exception] = None,
    ) -> Optional[Tuple[Dict, Dict]]:
        extra_params = extra_params or {}

        worker.setdefault("implementation", name)

        task = {"worker": worker}
        task_def = {"tags": {}}

        parameters.update(extra_params)
        config = make_transform_config(params=parameters, graph_cfg=graph_config)

        payload_builder = payload_builders[name]

        if inspect.isclass(raises) and issubclass(raises, Exception):
            with pytest.raises(raises):
                validate_schema(payload_builder.schema, worker, "schema error")
                payload_builder.builder(config, task, task_def)
        else:
            validate_schema(payload_builder.schema, worker, "schema error")
            payload_builder.builder(config, task, task_def)

            print("Dumping task_def for copy/paste:")
            pprint(task_def, indent=2)
            return task, task_def

    return inner


def test_bitrise_missing(build_payload):
    build_payload("scriptworker-bitrise", {}, raises=Exception)


def test_bitrise_missing_app(build_payload):
    build_payload(
        "scriptworker-bitrise", {"bitrise": {"workflows": ["foo"]}}, raises=Exception
    )


def test_bitrise_missing_workflows(build_payload):
    build_payload("scriptworker-bitrise", {"bitrise": {"app": "foo"}}, raises=Exception)


def test_bitrise_invalid_workflow_format(build_payload):
    build_payload(
        "scriptworker-bitrise",
        {"bitrise": {"app": "foo", "workflows": {"err": "nope"}}},
        raises=Exception,
    )


def test_bitrise_invalid_workflow_format2(build_payload):
    build_payload(
        "scriptworker-bitrise",
        {"bitrise": {"app": "foo", "workflows": [{"nope": ["wut"]}]}},
        raises=Exception,
    )


def test_bitrise_invalid_workflow_format3(build_payload):
    build_payload(
        "scriptworker-bitrise",
        {"bitrise": {"app": "foo", "workflows": [{"foo": {"bar": ["oops"]}}]}},
        raises=Exception,
    )


def test_bitrise_default_params(build_payload):
    assert build_payload(
        "scriptworker-bitrise",
        {"bitrise": {"app": "some-app", "workflows": ["bar", "baz"]}},
    )[1] == {
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
    }


def test_bitrise_pull_request(build_payload):
    assert build_payload(
        "scriptworker-bitrise",
        {"bitrise": {"app": "some-app", "workflows": ["bar"]}},
        extra_params={
            "tasks_for": "github-pull-request",
            "commit_message": "This is a commit",
            "pull_request_number": "123",
        },
    )[1] == {
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
    }


def test_bitrise_opposite_params(build_payload):
    assert build_payload(
        "scriptworker-bitrise",
        {"bitrise": {"app": "some-app", "workflows": ["bar"]}},
        extra_params={
            "base_ref": "",
            "base_repository": "",
            "head_ref": "",
            "head_tag": "some-tag",
            "tasks_for": "github-pull-request",
            "commit_message": "This is a commit",
            "pull_request_number": "123",
        },
    )[1] == {
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
    }


def test_bitrise_normalize_refs(build_payload):
    assert build_payload(
        "scriptworker-bitrise",
        {"bitrise": {"app": "some-app", "workflows": ["bar"]}},
        extra_params={
            "base_ref": "refs/heads/foo",
            "base_repository": "",
            "head_ref": "refs/heads/bar",
            "head_tag": "refs/tags/some-tag",
            "tasks_for": "github-pull-request",
            "commit_message": "This is a commit",
            "pull_request_number": "123",
        },
    )[1] == {
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
    }


def test_bitrise_normalize_refs_wrong_type(build_payload):
    assert build_payload(
        "scriptworker-bitrise",
        {"bitrise": {"app": "some-app", "workflows": ["bar"]}},
        extra_params={
            "base_ref": "refs/tags/foo",
            "base_repository": "",
            "head_ref": "refs/tags/bar",
            "head_tag": "refs/heads/some-tag",
            "tasks_for": "github-pull-request",
            "commit_message": "This is a commit",
            "pull_request_number": "123",
        },
    )[1] == {
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
    }


def test_bitrise_environments(build_payload):
    assert build_payload(
        "scriptworker-bitrise",
        {
            "bitrise": {
                "app": "some-app",
                "workflows": [
                    "foo",
                    {
                        "bar": [
                            {
                                "FOO": "bar",
                                "PATH": {"artifact-reference": "<build/target.zip>"},
                            },
                            {
                                "FOO": "notbar",
                                "PATH": {"artifact-reference": "<build/target.zip>"},
                            },
                        ]
                    },
                    {
                        "bar": [
                            {
                                "FOO": "bazzz",
                                "PATH": {"artifact-reference": "<build/target.zip>"},
                            },
                        ]
                    },
                ],
            }
        },
    )[1] == {
        "payload": {
            "global_params": {
                "branch": "default",
                "branch_repo_owner": "http://example.com/head/repo",
                "commit_hash": "abcdef",
            },
            "workflow_params": {
                "bar": [
                    {
                        "environments": [
                            {"mapped_to": "FOO", "value": "bar"},
                            {
                                "mapped_to": "PATH",
                                "value": {"artifact-reference": "<build/target.zip>"},
                            },
                        ]
                    },
                    {
                        "environments": [
                            {"mapped_to": "FOO", "value": "notbar"},
                            {
                                "mapped_to": "PATH",
                                "value": {"artifact-reference": "<build/target.zip>"},
                            },
                        ]
                    },
                    {
                        "environments": [
                            {"mapped_to": "FOO", "value": "bazzz"},
                            {
                                "mapped_to": "PATH",
                                "value": {"artifact-reference": "<build/target.zip>"},
                            },
                        ]
                    },
                ]
            },
        },
        "scopes": [
            "foo:bitrise:app:some-app",
            "foo:bitrise:workflow:bar",
            "foo:bitrise:workflow:foo",
        ],
        "tags": {"worker-implementation": "scriptworker"},
    }


def test_bitrise_artifact_prefix(build_payload):
    assert build_payload(
        "scriptworker-bitrise",
        {
            "bitrise": {
                "artifact_prefix": "public",
                "app": "some-app",
                "workflows": ["bar"],
            }
        },
    )[1] == {
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
    }


def test_build_shipit_payload(build_payload):
    assert build_payload("scriptworker-shipit", {"release-name": "foo"})[1] == {
        "payload": {"release_name": "foo"},
        "tags": {"worker-implementation": "scriptworker"},
    }


def test_build_signing_payload_invalid(build_payload):
    worker = {}
    build_payload("scriptworker-signing", worker=worker, raises=Exception)

    worker["signing-type"] = "release"
    build_payload("scriptworker-signing", worker=worker, raises=Exception)

    ua = worker["upstream-artifacts"] = [
        {
            "taskId": "abc",
            "taskType": "build",
            "paths": ["foo/bar", "test.dmg"],
            "formats": ["gpg", "gcp_prod_autograph_gpg"],
        }
    ]
    for key in ("taskId", "taskType", "paths", "formats"):
        val = ua[0].pop(key)
        build_payload("scriptworker-signing", worker=worker, raises=Exception)
        ua[0][key] = val


def test_build_signing_payload_basic(build_payload):
    worker = {
        "signing-type": "release",
        "upstream-artifacts": [
            {
                "taskId": "abc",
                "taskType": "build",
                "paths": ["foo/bar"],
                "formats": ["gpg"],
            }
        ],
    }
    task, task_def = build_payload("scriptworker-signing", worker=worker)
    assert task_def == {
        "payload": {
            "upstreamArtifacts": [
                {
                    "formats": ["gpg"],
                    "paths": ["foo/bar"],
                    "taskId": "abc",
                    "taskType": "build",
                }
            ],
        },
        "scopes": [
            "foo:signing:cert:release",
            "foo:signing:format:gpg",
        ],
        "tags": {"worker-implementation": "scriptworker"},
    }
    assert task["attributes"] == {
        "release_artifacts": [
            "foo/bar",
        ]
    }


def test_build_signing_payload_dmg(build_payload):
    worker = {
        "max-run-time": 3600,
        "signing-type": "release",
        "upstream-artifacts": [
            {
                "taskId": "abc",
                "taskType": "build",
                "paths": ["test.dmg"],
                "formats": ["gpg"],
            }
        ],
    }
    task, task_def = build_payload("scriptworker-signing", worker=worker)
    assert task_def == {
        "payload": {
            "maxRunTime": 3600,
            "upstreamArtifacts": [
                {
                    "formats": ["gpg"],
                    "paths": ["test.dmg"],
                    "taskId": "abc",
                    "taskType": "build",
                }
            ],
        },
        "scopes": [
            "foo:signing:cert:release",
            "foo:signing:format:gpg",
        ],
        "tags": {"worker-implementation": "scriptworker"},
    }
    assert task["attributes"] == {"release_artifacts": ["test.tar.gz"]}


def test_build_signing_payload_gpg_asc(build_payload):
    worker = {
        "max-run-time": 3600,
        "signing-type": "release",
        "upstream-artifacts": [
            {
                "taskId": "abc",
                "taskType": "build",
                "paths": ["foo/bar"],
                "formats": ["gcp_prod_autograph_gpg"],
            }
        ],
    }
    task, task_def = build_payload("scriptworker-signing", worker=worker)
    assert task_def == {
        "payload": {
            "maxRunTime": 3600,
            "upstreamArtifacts": [
                {
                    "formats": ["gcp_prod_autograph_gpg"],
                    "paths": ["foo/bar"],
                    "taskId": "abc",
                    "taskType": "build",
                }
            ],
        },
        "scopes": [
            "foo:signing:cert:release",
            "foo:signing:format:gcp_prod_autograph_gpg",
        ],
        "tags": {"worker-implementation": "scriptworker"},
    }
    assert task["attributes"] == {
        "release_artifacts": [
            "foo/bar",
            "foo/bar.asc",
        ]
    }
