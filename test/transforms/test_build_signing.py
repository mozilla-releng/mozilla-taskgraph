import pytest
from taskgraph.util.schema import SchemaValidationError

from mozilla_taskgraph.transforms.build_signing import (
    add_signed_routes,
    define_upstream_artifacts,
)
from mozilla_taskgraph.transforms.build_signing import (
    transforms as build_signing_transforms,
)

from ..conftest import make_task


def _dep(routes=None, attributes=None, kind="build"):
    return make_task(
        "dep-label",
        kind=kind,
        task_def={"routes": routes or []},
        attributes=attributes or {},
    )


def _task(dep, **extra):
    task = {"attributes": {"primary-dependency-label": dep.label}}
    task.update(extra)
    return task


def test_add_signed_routes(make_transform_config):
    # The test graph config uses `trust-domain: test`.
    dep = _dep(
        routes=[
            "index.test.v2.mozilla-central.latest.firefox.win64",
            "index.other.v2.mozilla-central.latest.firefox.win64",
            "tc-treeherder.v2.mozilla-central.abcdef",
        ]
    )
    config = make_transform_config(kind_dependencies_tasks={dep.label: dep})

    [task] = list(add_signed_routes(config, [_task(dep)]))

    # Only this trust-domain's index route is mirrored, with `.signed` inserted
    # after the project; other trust domains and non-index routes are ignored.
    assert task["routes"] == [
        "index.test.v2.mozilla-central.signed.latest.firefox.win64"
    ]


def test_add_signed_routes_disabled(make_transform_config):
    dep = _dep(routes=["index.test.v2.mozilla-central.latest.firefox.win64"])
    config = make_transform_config(kind_dependencies_tasks={dep.label: dep})

    [task] = list(
        add_signed_routes(config, [_task(dep, **{"enable-signing-routes": False})])
    )
    assert task["routes"] == []


def test_define_upstream_artifacts(make_transform_config):
    dep = _dep(attributes={"build_platform": "win64-shippable", "shippable": True})
    config = make_transform_config(kind_dependencies_tasks={dep.label: dep})

    task = _task(
        dep,
        **{
            "signing-artifacts": [
                {
                    "paths": ["public/build/target.zip"],
                    "formats": ["autograph_authenticode"],
                }
            ]
        },
    )
    [task] = list(define_upstream_artifacts(config, [task]))

    assert task["upstream-artifacts"] == [
        {
            "taskId": {"task-reference": "<build>"},
            "taskType": "build",
            "paths": ["public/build/target.zip"],
            "formats": ["autograph_authenticode"],
        }
    ]
    # Curated attributes copied from the dependency, plus signed marker.
    assert task["attributes"]["build_platform"] == "win64-shippable"
    assert task["attributes"]["shippable"] is True
    assert task["attributes"]["signed"] is True


def test_signing_artifacts_is_required(make_transform_config):
    """A project that forgets to populate the key gets an error, not a signing
    task with an empty payload."""
    dep = _dep()
    config = make_transform_config(kind_dependencies_tasks={dep.label: dep})

    with pytest.raises(SchemaValidationError):
        list(build_signing_transforms(config, [_task(dep)]))


def test_signing_artifacts_rejects_malformed_spec(make_transform_config):
    dep = _dep()
    config = make_transform_config(kind_dependencies_tasks={dep.label: dep})
    task = _task(dep, **{"signing-artifacts": [{"paths": ["a"], "format": ["b"]}]})

    with pytest.raises(SchemaValidationError):
        list(build_signing_transforms(config, [task]))


def test_define_upstream_artifacts_notarization_task_type(make_transform_config):
    dep = _dep(attributes={"build_platform": "macosx64"}, kind="mac-notarization")
    config = make_transform_config(kind_dependencies_tasks={dep.label: dep})

    task = _task(
        dep,
        **{"signing-artifacts": [{"paths": ["a/target.dmg"], "formats": ["apple"]}]},
    )
    [task] = list(define_upstream_artifacts(config, [task]))

    assert task["upstream-artifacts"][0]["taskType"] == "scriptworker"
    assert task["upstream-artifacts"][0]["taskId"] == {
        "task-reference": "<mac-notarization>"
    }
