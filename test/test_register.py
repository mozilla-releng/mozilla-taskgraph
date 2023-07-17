from contextlib import nullcontext as does_not_raise

import pytest
from taskgraph.transforms.task import payload_builders

from mozilla_taskgraph import register


def test_payload_builders(graph_config):
    expected_payload_builders = {
        "scriptworker-shipit",
    }
    register(graph_config)
    missing = expected_payload_builders - set(payload_builders)
    if missing:
        print("The following expected payload builders are missing:")
        print("  " + "\n  ".join(sorted(missing)))
    assert not missing


@pytest.mark.parametrize(
    "extra_config,expectation",
    (
        pytest.param({}, does_not_raise(), id="no_extra_config"),
        pytest.param(
            {"shipit": {"product": "foo"}},
            does_not_raise(),
            id="shipit_valid",
        ),
        pytest.param(
            {"shipit": {"product": "foo", "extra": "bar"}},
            pytest.raises(Exception),
            id="shipit_invalid",
        ),
    ),
)
def test_graph_config(make_graph_config, extra_config, expectation):
    # Shipit config is valid
    graph_config = make_graph_config(extra_config=extra_config)
    with expectation:
        register(graph_config)
