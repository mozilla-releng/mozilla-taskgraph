# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pytest

from mozilla_taskgraph.util.attributes import release_level

FIREFOX_BRANCHES = ["main", "beta", "release", "esr140"]
RELEASE_BRANCHES = {
    "firefox": FIREFOX_BRANCHES,
    "mozilla-central": True,
}


@pytest.mark.parametrize(
    "release_branches,params,expected",
    (
        # Not level 3 -> always staging, regardless of branch.
        (RELEASE_BRANCHES, {"level": "1", "project": "mozilla-central"}, "staging"),
        (
            RELEASE_BRANCHES,
            {"level": "1", "project": "firefox", "head_ref": "refs/heads/beta"},
            "staging",
        ),
        # Empty `release-branches` mapping -> staging.
        (
            {},
            {"level": "3", "project": "firefox", "head_ref": "refs/heads/beta"},
            "staging",
        ),
        # Project not listed in the mapping -> staging (e.g. autoland).
        (RELEASE_BRANCHES, {"level": "3", "project": "autoland"}, "staging"),
        # Whole project is a release project (Mercurial model).
        (RELEASE_BRANCHES, {"level": "3", "project": "mozilla-central"}, "production"),
        # Git monorepo model: only listed branches are production.
        (
            RELEASE_BRANCHES,
            {"level": "3", "project": "firefox", "head_ref": "refs/heads/beta"},
            "production",
        ),
        (
            RELEASE_BRANCHES,
            {"level": "3", "project": "firefox", "head_ref": "refs/heads/test"},
            "staging",
        ),
        # Only refs/heads/* match, not tags.
        (
            RELEASE_BRANCHES,
            {"level": "3", "project": "firefox", "head_ref": "refs/tags/beta"},
            "staging",
        ),
    ),
)
def test_release_level(release_branches, params, expected):
    assert release_level(release_branches, params) == expected
