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
        extra_config={"scriptworker": {"scope-prefix": "foo"}},
    )

    def inner(
        name: str,
        worker: dict,
        extra_params: Optional[Dict] = None,
        raises: Optional[Exception] = None,
    ) -> Optional[Tuple[Dict, Dict]]:
        extra_params = extra_params or {}

        worker.setdefault("implementation", name)

        task = {"worker": worker, "shipping-product": "product"}
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
        ],
        "tags": {"worker-implementation": "scriptworker"},
    }
    assert task["attributes"] == {
        "release_artifacts": [
            "foo/bar",
            "foo/bar.asc",
        ]
    }


def test_lando_android_l10n_import(build_payload):
    worker = {
        "lando-repo": "testrepo",
        "actions": [
            {
                "android-l10n-import": {
                    "from-repo-url": "https://from",
                    "toml-info": [
                        {
                            "toml-path": "foo/bar/l10n.toml",
                            "dest-path": "foo-bar",
                        }
                    ],
                },
            }
        ],
    }
    _, task_def = build_payload("scriptworker-lando", worker=worker)
    assert task_def == {
        "payload": {
            "actions": ["android_l10n_import"],
            "lando_repo": "testrepo",
            "android_l10n_import_info": {
                "from_repo_url": "https://from",
                "toml_info": [
                    {"toml_path": "foo/bar/l10n.toml", "dest_path": "foo-bar"},
                ],
            },
        },
        "scopes": [
            "project:releng:lando:action:android_l10n_import",
            "project:releng:lando:repo:testrepo",
        ],
        "tags": {"worker-implementation": "scriptworker"},
    }


def test_lando_android_l10n_sync(build_payload):
    worker = {
        "lando-repo": "testrepo",
        "actions": [
            {
                "android-l10n-sync": {
                    "from-branch": "branchy",
                    "toml-info": [
                        {
                            "toml-path": "foo/bar/l10n.toml",
                        }
                    ],
                },
            }
        ],
    }
    _, task_def = build_payload("scriptworker-lando", worker=worker)
    assert task_def == {
        "payload": {
            "actions": ["android_l10n_sync"],
            "lando_repo": "testrepo",
            "android_l10n_sync_info": {
                "from_branch": "branchy",
                "toml_info": [
                    {
                        "toml_path": "foo/bar/l10n.toml",
                    },
                ],
            },
        },
        "scopes": [
            "project:releng:lando:action:android_l10n_sync",
            "project:releng:lando:repo:testrepo",
        ],
        "tags": {"worker-implementation": "scriptworker"},
    }


def test_lando_l10n_bump_mismatched_urls(build_payload):
    worker = {
        "lando-repo": "testrepo",
        "dontbuild": True,
        "ignore-closed-tree": True,
        "actions": [
            {
                "l10n-bump": [
                    {
                        "name": "l10n",
                        "path": "foo/bar/changesets.json",
                        "l10n-repo-url": "https://l10n",
                        "l10n-repo-target-branch": "branchy",
                        "ignore-config": {"ab": ["foo"]},
                        "platform-configs": [
                            {
                                "platforms": ["p1", "p2"],
                                "path": "foo/bar/locales",
                            },
                        ],
                    },
                    {
                        "name": "l10n2",
                        "path": "foo/baz/changesets.json",
                        "l10n-repo-url": "https://l10n2",
                        "l10n-repo-target-branch": "branchy",
                        "ignore-config": {"ab": ["foo"]},
                        "platform-configs": [
                            {
                                "platforms": ["p1", "p2"],
                                "path": "foo/bar/locales",
                            },
                        ],
                    },
                ],
            }
        ],
    }
    try:
        build_payload("scriptworker-lando", worker=worker)
        assert False, "should've raised an exception"
    except Exception as e:
        assert "Must use the same l10n-repo-url for all files" in e.args[0]


def test_lando_l10n_bump(build_payload):
    worker = {
        "lando-repo": "testrepo",
        "dontbuild": True,
        "ignore-closed-tree": True,
        "actions": [
            {
                "l10n-bump": [
                    {
                        "name": "l10n",
                        "path": "foo/bar/changesets.json",
                        "l10n-repo-url": "https://l10n",
                        "l10n-repo-target-branch": "branchy",
                        "ignore-config": {"ab": ["foo"]},
                        "platform-configs": [
                            {
                                "platforms": ["p1", "p2"],
                                "path": "foo/bar/locales",
                            },
                        ],
                    },
                    {
                        "name": "l10n2",
                        "path": "foo/baz/changesets.json",
                        "l10n-repo-url": "https://l10n",
                        "l10n-repo-target-branch": "branchy",
                        "ignore-config": {"ab": ["foo"]},
                        "platform-configs": [
                            {
                                "platforms": ["p1", "p2"],
                                "path": "foo/bar/locales",
                            },
                        ],
                    },
                ],
            }
        ],
    }
    _, task_def = build_payload("scriptworker-lando", worker=worker)
    assert task_def == {
        "payload": {
            "actions": ["l10n_bump"],
            "lando_repo": "testrepo",
            "dontbuild": True,
            "ignore_closed_tree": True,
            "l10n_bump_info": [
                {
                    "name": "l10n",
                    "path": "foo/bar/changesets.json",
                    "l10n_repo_url": "https://l10n",
                    "l10n_repo_target_branch": "branchy",
                    "ignore_config": {
                        "ab": ["foo"],
                    },
                    "platform_configs": [
                        {
                            "platforms": ["p1", "p2"],
                            "path": "foo/bar/locales",
                        },
                    ],
                },
                {
                    "name": "l10n2",
                    "path": "foo/baz/changesets.json",
                    "l10n_repo_url": "https://l10n",
                    "l10n_repo_target_branch": "branchy",
                    "ignore_config": {
                        "ab": ["foo"],
                    },
                    "platform_configs": [
                        {
                            "platforms": ["p1", "p2"],
                            "path": "foo/bar/locales",
                        },
                    ],
                },
            ],
        },
        "scopes": [
            "project:releng:lando:action:l10n_bump",
            "project:releng:lando:repo:testrepo",
        ],
        "tags": {"worker-implementation": "scriptworker"},
    }


@pytest.mark.parametrize(
    "types,expected",
    (
        pytest.param(
            ["buildN"],
            ["PRODUCT_99_0_BUILD1"],
            id="buildN",
        ),
        pytest.param(
            ["release"],
            ["PRODUCT_99_0_RELEASE"],
            id="release",
        ),
        pytest.param(
            ["buildN", "release"],
            ["PRODUCT_99_0_BUILD1", "PRODUCT_99_0_RELEASE"],
            id="buildN_and_release",
        ),
    ),
)
def test_lando_tag(build_payload, types, expected):
    worker = {
        "lando-repo": "testrepo",
        "actions": [
            {
                "tag": {
                    "types": types,
                    "hg-repo-url": "https://hg/repo",
                }
            }
        ],
    }
    _, task_def = build_payload("scriptworker-lando", worker=worker)
    assert task_def == {
        "payload": {
            "actions": ["tag"],
            "lando_repo": "testrepo",
            "tag_info": {
                "hg_repo_url": "https://hg/repo",
                "revision": "abcdef",
                "tags": expected,
            },
        },
        "scopes": [
            "project:releng:lando:action:tag",
            "project:releng:lando:repo:testrepo",
        ],
        "tags": {"worker-implementation": "scriptworker"},
    }


def test_lando_version_bump(build_payload):
    worker = {
        "lando-repo": "testrepo",
        "actions": [
            {
                "version-bump": {
                    "bump-files": [
                        "foo/bar/a.txt",
                        "another/file.txt",
                    ],
                }
            }
        ],
    }
    _, task_def = build_payload("scriptworker-lando", worker=worker)
    assert task_def == {
        "payload": {
            "actions": ["version_bump"],
            "lando_repo": "testrepo",
            "version_bump_info": {
                "files": [
                    "foo/bar/a.txt",
                    "another/file.txt",
                ],
                "next_version": "100.0",
            },
        },
        "scopes": [
            "project:releng:lando:action:version_bump",
            "project:releng:lando:repo:testrepo",
        ],
        "tags": {"worker-implementation": "scriptworker"},
    }


@pytest.mark.parametrize(
    "dry_run", (pytest.param(True, id="dry_run"), pytest.param(False, id="not_dry_run"))
)
def test_lando_merge_bump_esr(build_payload, dry_run):
    worker = {
        "lando-repo": "testrepo",
        "force-dry-run": dry_run,
        "actions": [
            {
                "esr-bump": {
                    "fetch-version-from": "version.txt",
                    "version-files": [
                        {
                            "filename": "version.txt",
                            "version-bump": "minor",
                        },
                        {
                            "filename": "other.txt",
                            "new-suffix": "esr",
                            "version-bump": "minor",
                        },
                    ],
                    "to-branch": "to-b",
                }
            }
        ],
    }
    _, task_def = build_payload("scriptworker-lando", worker=worker)
    expected = {
        "payload": {
            "actions": ["merge_day"],
            "lando_repo": "testrepo",
            "merge_info": {
                "fetch_version_from": "version.txt",
                "version_files": [
                    {
                        "filename": "version.txt",
                        "version_bump": "minor",
                    },
                    {
                        "filename": "other.txt",
                        "new_suffix": "esr",
                        "version_bump": "minor",
                    },
                ],
                "to_branch": "to-b",
            },
        },
        "scopes": [
            "project:releng:lando:action:merge_day",
            "project:releng:lando:repo:testrepo",
        ],
        "tags": {"worker-implementation": "scriptworker"},
    }
    if dry_run:
        expected["payload"]["dry_run"] = dry_run

    assert task_def == expected


def test_lando_merge_bump_main(build_payload):
    worker = {
        "lando-repo": "testrepo",
        "actions": [
            {
                "main-bump": {
                    "fetch-version-from": "version.txt",
                    "version-files": [
                        {
                            "filename": "version.txt",
                            "new-suffix": "a1",
                            "version-bump": "minor",
                        },
                        {
                            "filename": "other.txt",
                            "new-suffix": "a1",
                            "version-bump": "minor",
                        },
                    ],
                    "to-branch": "to-b",
                    "replacements": [
                        [
                            "filename",
                            "before.{current_weave_version}",
                            "after.{current_weave_version}",
                        ]
                    ],
                    "regex-replacements": [
                        ["filename", "foo [0-9]+.0", "foo {next_major_version}.0"]
                    ],
                    "end-tag": "PRODUCT_{major_version}_END",
                }
            }
        ],
    }
    _, task_def = build_payload("scriptworker-lando", worker=worker)
    assert task_def == {
        "payload": {
            "actions": ["merge_day"],
            "lando_repo": "testrepo",
            "merge_info": {
                "fetch_version_from": "version.txt",
                "version_files": [
                    {
                        "filename": "version.txt",
                        "new_suffix": "a1",
                        "version_bump": "minor",
                    },
                    {
                        "filename": "other.txt",
                        "new_suffix": "a1",
                        "version_bump": "minor",
                    },
                ],
                "replacements": [
                    [
                        "filename",
                        "before.{current_weave_version}",
                        "after.{current_weave_version}",
                    ]
                ],
                "regex_replacements": [
                    ["filename", "foo [0-9]+.0", "foo {next_major_version}.0"]
                ],
                "end_tag": "PRODUCT_{major_version}_END",
                "to_branch": "to-b",
            },
        },
        "scopes": [
            "project:releng:lando:action:merge_day",
            "project:releng:lando:repo:testrepo",
        ],
        "tags": {"worker-implementation": "scriptworker"},
    }


def test_lando_merge_early_to_late_beta(build_payload):
    worker = {
        "lando-repo": "testrepo",
        "actions": [
            {
                "early-to-late-beta": {
                    "replacements": [
                        [
                            "defines",
                            "foo=1",
                            "foo=",
                        ]
                    ],
                    "to-branch": "to-b",
                }
            }
        ],
    }
    _, task_def = build_payload("scriptworker-lando", worker=worker)
    assert task_def == {
        "payload": {
            "actions": ["merge_day"],
            "lando_repo": "testrepo",
            "merge_info": {
                "replacements": [
                    [
                        "defines",
                        "foo=1",
                        "foo=",
                    ]
                ],
                "to_branch": "to-b",
            },
        },
        "scopes": [
            "project:releng:lando:action:merge_day",
            "project:releng:lando:repo:testrepo",
        ],
        "tags": {"worker-implementation": "scriptworker"},
    }


def test_lando_merge_main_to_beta(build_payload):
    worker = {
        "lando-repo": "testrepo",
        "matrix-rooms": ["!foobar:mozilla.org"],
        "actions": [
            {
                "uplift": {
                    "fetch-version-from": "version.txt",
                    "version-files": [
                        {
                            "filename": "version.txt",
                        },
                        {
                            "filename": "other.txt",
                            "new-suffix": "b1",
                        },
                    ],
                    "replacements": [
                        [
                            "mozconfig",
                            "nightly",
                            "official",
                        ]
                    ],
                    "base-tag": "PRODUCT_{major_version}_BASE",
                    "end-tag": "PRODUCT_{major_version}_END",
                    "to-branch": "to-b",
                    "from-branch": "from-b",
                    "l10n-bump-info": [
                        {
                            "name": "l10n",
                            "path": "foo/bar/changesets.json",
                            "l10n-repo-url": "https://l10n",
                            "l10n-repo-target-branch": "branchy",
                            "ignore-config": {"ab": ["foo"]},
                            "platform-configs": [
                                {
                                    "platforms": ["p1", "p2"],
                                    "path": "foo/bar/locales",
                                },
                            ],
                        }
                    ],
                }
            }
        ],
    }
    _, task_def = build_payload("scriptworker-lando", worker=worker)
    assert task_def == {
        "payload": {
            "actions": ["merge_day"],
            "lando_repo": "testrepo",
            "merge_info": {
                "fetch_version_from": "version.txt",
                "version_files": [
                    {
                        "filename": "version.txt",
                    },
                    {
                        "filename": "other.txt",
                        "new_suffix": "b1",
                    },
                ],
                "replacements": [
                    [
                        "mozconfig",
                        "nightly",
                        "official",
                    ]
                ],
                "merge_old_head": True,
                "base_tag": "PRODUCT_{major_version}_BASE",
                "end_tag": "PRODUCT_{major_version}_END",
                "to_branch": "to-b",
                "from_branch": "from-b",
                "l10n_bump_info": [
                    {
                        "name": "l10n",
                        "path": "foo/bar/changesets.json",
                        "l10n_repo_url": "https://l10n",
                        "l10n_repo_target_branch": "branchy",
                        "ignore_config": {
                            "ab": ["foo"],
                        },
                        "platform_configs": [
                            {
                                "platforms": ["p1", "p2"],
                                "path": "foo/bar/locales",
                            },
                        ],
                    }
                ],
            },
        },
        "routes": [
            "notify.matrix-room.!foobar:mozilla.org.on-pending",
            "notify.matrix-room.!foobar:mozilla.org.on-resolved",
        ],
        "scopes": [
            "project:releng:lando:action:merge_day",
            "project:releng:lando:repo:testrepo",
            "queue:route:notify.matrix-room.*",
        ],
        "tags": {"worker-implementation": "scriptworker"},
    }


def test_lando_merge_beta_to_release(build_payload):
    worker = {
        "lando-repo": "testrepo",
        "matrix-rooms": ["!foobar:mozilla.org"],
        "actions": [
            {
                "uplift": {
                    "fetch-version-from": "version.txt",
                    "version-files": [
                        {
                            "filename": "version.txt",
                        },
                        {
                            "filename": "other.txt",
                            "new-suffix": "b1",
                        },
                    ],
                    "replacements": [
                        [
                            ".arcconfig",
                            "BETA",
                            "RELEASE",
                        ]
                    ],
                    "base-tag": "PRODUCT_{major_version}_BASE",
                    "end-tag": "PRODUCT_{major_version}_END",
                    "to-branch": "to-b",
                    "from-branch": "from-b",
                }
            }
        ],
    }
    _, task_def = build_payload("scriptworker-lando", worker=worker)
    assert task_def == {
        "payload": {
            "actions": ["merge_day"],
            "lando_repo": "testrepo",
            "merge_info": {
                "fetch_version_from": "version.txt",
                "version_files": [
                    {
                        "filename": "version.txt",
                    },
                    {
                        "filename": "other.txt",
                        "new_suffix": "b1",
                    },
                ],
                "replacements": [
                    [
                        ".arcconfig",
                        "BETA",
                        "RELEASE",
                    ]
                ],
                "merge_old_head": True,
                "base_tag": "PRODUCT_{major_version}_BASE",
                "end_tag": "PRODUCT_{major_version}_END",
                "to_branch": "to-b",
                "from_branch": "from-b",
            },
        },
        "routes": [
            "notify.matrix-room.!foobar:mozilla.org.on-pending",
            "notify.matrix-room.!foobar:mozilla.org.on-resolved",
        ],
        "scopes": [
            "project:releng:lando:action:merge_day",
            "project:releng:lando:repo:testrepo",
            "queue:route:notify.matrix-room.*",
        ],
        "tags": {"worker-implementation": "scriptworker"},
    }
