# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pytest

from mozilla_taskgraph.util.attributes import release_level

FIREFOX_BRANCHES = ["main", "beta", "release", "esr140"]


@pytest.mark.parametrize(
    "params,expected",
    (
        # Not level 3 -> always staging, regardless of branch.
        ({"level": "1", "release_branches": True}, "staging"),
        (
            {
                "level": "1",
                "release_branches": FIREFOX_BRANCHES,
                "head_ref": "refs/heads/beta",
            },
            "staging",
        ),
        # No release branches for the project -> staging (e.g. autoland).
        ({"level": "3", "release_branches": None}, "staging"),
        # Whole project is a release project (Mercurial model).
        ({"level": "3", "release_branches": True}, "production"),
        # Git monorepo model: only listed branches are production.
        (
            {
                "level": "3",
                "release_branches": FIREFOX_BRANCHES,
                "head_ref": "refs/heads/beta",
            },
            "production",
        ),
        (
            {
                "level": "3",
                "release_branches": FIREFOX_BRANCHES,
                "head_ref": "refs/heads/test",
            },
            "staging",
        ),
        # Only refs/heads/* match, not tags.
        (
            {
                "level": "3",
                "release_branches": FIREFOX_BRANCHES,
                "head_ref": "refs/tags/beta",
            },
            "staging",
        ),
    ),
)
def test_release_level(params, expected):
    assert release_level(params) == expected
