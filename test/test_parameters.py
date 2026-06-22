# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pytest

from mozilla_taskgraph.parameters import set_release_branches


@pytest.mark.parametrize(
    "release_branches,project,expected",
    (
        # No `release-branches` config at all.
        (None, "some-project", None),
        # Project not listed.
        ({"firefox": ["main"]}, "autoland", None),
        # Whole project is a release project.
        ({"mozilla-central": True}, "mozilla-central", True),
        # Project mapped to a list of branches.
        ({"firefox": ["main", "beta"]}, "firefox", ["main", "beta"]),
    ),
)
def test_set_release_branches(
    make_graph_config, parameters, release_branches, project, expected
):
    extra_config = {}
    if release_branches is not None:
        extra_config["release-branches"] = release_branches

    graph_config = make_graph_config(extra_config=extra_config)
    parameters["project"] = project

    set_release_branches(graph_config, parameters)
    assert parameters["release_branches"] == expected
