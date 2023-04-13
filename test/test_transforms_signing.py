import pytest
from taskgraph.util.templates import merge

from mozilla_taskgraph.transforms.scriptworker.signing import (
    transforms as signing_transforms,
)

DEFAULT_EXPECTED = {
    "attributes": {"artifacts": {}, "build-type": "linux", "signed": True},
    "name": "task",
    "worker": {
        "signing-type": "dep-signing",
        "upstream-artifacts": [],
    },
    "worker-type": "dep-signing",
}


def assert_level_3(task):
    expected = merge(
        DEFAULT_EXPECTED,
        {
            "worker-type": "signing",
            "worker": {
                "signing-type": "release-signing",
                "upstream-artifacts": [
                    {"paths": ["build.zip"], "formats": ["autograph_gpg"]}
                ],
            },
        },
    )
    assert task == expected


def assert_level_1(task):
    expected = merge(
        DEFAULT_EXPECTED,
        {
            "worker": {
                "upstream-artifacts": [
                    {"paths": ["build.zip"], "formats": ["autograph_gpg"]}
                ],
            }
        },
    )
    assert task == expected


def assert_macos_worker_type(task):
    assert task["worker-type"] == "macos-dep-signing"


def assert_ignore_artifacts(task):
    assert task["worker"]["upstream-artifacts"] == [
        {
            "formats": ["autograph_gpg"],
            "paths": ["build.zip"],
        }
    ]


@pytest.mark.parametrize(
    "params,task",
    (
        pytest.param(
            # params
            {"level": "3"},
            # task
            {
                "signing": {
                    "format": "autograph_gpg",
                },
                "worker": {"upstream-artifacts": [{"paths": ["build.zip"]}]},
            },
            id="level_3",
        ),
        pytest.param(
            # params
            {"level": "1"},
            # task
            {
                "signing": {
                    "format": "autograph_gpg",
                },
                "worker": {"upstream-artifacts": [{"paths": ["build.zip"]}]},
            },
            id="level_1",
        ),
        pytest.param(
            # params
            {"level": "1"},
            # task
            {
                "attributes": {
                    "build-type": "macos",
                },
                "signing": {
                    "format": "autograph_gpg",
                },
            },
            id="macos_worker_type",
        ),
        pytest.param(
            # params
            {"level": "1"},
            # task
            {
                "signing": {
                    "format": "autograph_gpg",
                    "ignore-artifacts": [r".*\.txt"],
                },
                "worker": {"upstream-artifacts": [{"paths": ["build.zip", "log.txt"]}]},
            },
            id="ignore_artifacts",
        ),
    ),
)
def test_signing_transforms(
    request, make_transform_config, run_transform, params, task
):
    task.setdefault("name", "task")
    task.setdefault("worker", {}).setdefault("upstream-artifacts", [])
    attributes = task.setdefault("attributes", {})
    attributes.setdefault("artifacts", {})
    attributes.setdefault("build-type", "linux")

    config = make_transform_config()
    config.params.update(params)

    tasks = run_transform(signing_transforms, task, config)
    assert len(tasks) == 1

    param_id = request.node.callspec.id
    assert_func = globals()[f"assert_{param_id}"]
    assert_func(tasks[0])
