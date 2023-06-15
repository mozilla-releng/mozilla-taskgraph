from pprint import pprint

import pytest

from mozilla_taskgraph.transforms.scriptworker.release_artifacts import (
    transforms as release_artifacts_transforms,
)


def assert_no_release_artifacts(task):
    assert task == {"worker-type": "foo"}


def assert_absolute_path(e):
    assert isinstance(e, Exception)


def assert_docker_worker(task):
    assert task == {
        "attributes": {
            "release-artifacts": [
                {
                    "name": "public/build/foo.txt",
                    "path": "/builds/worker/artifacts/foo.txt",
                    "type": "file",
                }
            ]
        },
        "worker-type": "t-linux",
        "worker": {
            "artifacts": [
                {
                    "name": "public/build/foo.txt",
                    "path": "/builds/worker/artifacts/foo.txt",
                    "type": "file",
                }
            ]
        },
    }


def assert_generic_worker(task):
    assert task == {
        "attributes": {
            "release-artifacts": [
                {
                    "name": "public/build/foo.txt",
                    "path": "artifacts/foo.txt",
                    "type": "file",
                }
            ]
        },
        "worker-type": "b-linux",
        "worker": {
            "artifacts": [
                {
                    "name": "public/build/foo.txt",
                    "path": "artifacts/foo.txt",
                    "type": "file",
                }
            ]
        },
    }


@pytest.mark.parametrize(
    "task",
    (
        pytest.param(
            {"worker-type": "foo"},
            id="no_release_artifacts",
        ),
        pytest.param(
            {"worker-type": "t-linux", "release-artifacts": ["/foo.txt"]},
            id="absolute_path",
        ),
        pytest.param(
            {"worker-type": "t-linux", "release-artifacts": ["foo.txt"]},
            id="docker_worker",
        ),
        pytest.param(
            {"worker-type": "b-linux", "release-artifacts": ["foo.txt"]},
            id="generic_worker",
        ),
    ),
)
def test_release_artifacts(request, run_transform, task):
    try:
        result = run_transform(release_artifacts_transforms, task)
        assert len(result) == 1
        result = result[0]

        print("Dumping result:")
        pprint(result, indent=2)
    except Exception as e:
        result = e

    param_id = request.node.callspec.id
    assert_func = globals()[f"assert_{param_id}"]
    assert_func(result)
