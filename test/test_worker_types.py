from mozilla_taskgraph import worker_types


def test_build_shipit_payload():
    task = {"worker": {"release-name": "foo"}}
    task_def = {"tags": {}}
    worker_types.build_shipit_payload(None, task, task_def)
    assert task_def == {
        "payload": {"release_name": "foo"},
        "tags": {"worker-implementation": "scriptworker"},
    }
