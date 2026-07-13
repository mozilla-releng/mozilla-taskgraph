from pprint import pprint

from mozilla_taskgraph.transforms.build_signing import transforms

from ..conftest import make_task


def _make_dep(
    routes=None, shippable=True, build_platform="win64-shippable", kind="build"
):
    return make_task(
        f"{kind}-win",
        kind=kind,
        attributes={"build_platform": build_platform, "shippable": shippable},
        task_def={"routes": routes or []},
    )


def _make_job(dep):
    return {
        "attributes": {"primary-dependency-label": dep.label},
        "dependencies": {dep.kind: dep.label},
    }


def _run(run_transform, make_transform_config, dep, job):
    config = make_transform_config(kind_dependencies_tasks={dep.label: dep})
    result = run_transform(transforms, job, config=config)
    assert len(result) == 1
    pprint(result[0], indent=2)
    return result[0]


def test_signed_routes_and_upstream_artifacts(run_transform, make_transform_config):
    dep = _make_dep(
        routes=[
            "index.gecko.v2.mozilla-central.latest.firefox.win64",
            "index.some.other.route",
        ]
    )
    task = _run(run_transform, make_transform_config, dep, _make_job(dep))

    # gecko.v2 route gets ``.signed`` inserted; non-gecko routes are dropped
    assert task["routes"] == [
        "index.gecko.v2.mozilla-central.signed.latest.firefox.win64"
    ]

    ua = task["upstream-artifacts"]
    assert ua[0]["taskId"] == {"task-reference": "<build>"}
    assert ua[0]["taskType"] == "build"
    assert ua[0]["paths"] == ["public/build/setup.exe"]
    assert ua[1]["paths"] == ["public/build/target.zip"]


def test_enable_signing_routes_false(run_transform, make_transform_config):
    dep = _make_dep(routes=["index.gecko.v2.mozilla-central.latest.firefox.win64"])
    job = _make_job(dep)
    job["enable-signing-routes"] = False
    task = _run(run_transform, make_transform_config, dep, job)
    assert task["routes"] == []


def test_non_shippable_dep_has_no_routes(run_transform, make_transform_config):
    dep = _make_dep(
        routes=["index.gecko.v2.mozilla-central.latest.firefox.win64"],
        shippable=False,
    )
    task = _run(run_transform, make_transform_config, dep, _make_job(dep))
    assert task["routes"] == []


def test_notarization_dep_sets_scriptworker_task_type(
    run_transform, make_transform_config
):
    dep = _make_dep(build_platform="macosx64-shippable", kind="build-mac-notarization")
    task = _run(run_transform, make_transform_config, dep, _make_job(dep))
    assert task["upstream-artifacts"][0]["taskType"] == "scriptworker"
    assert task["upstream-artifacts"][0]["taskId"] == {
        "task-reference": "<build-mac-notarization>"
    }
