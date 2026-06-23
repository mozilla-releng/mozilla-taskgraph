# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import re


def release_level(release_branches: dict, params: dict):
    """Whether this is a production release or not.

    ``release_branches`` is the graph config's ``release-branches`` mapping of
    project to the branches considered "production" for it. A value of ``True``
    for a project means every branch of that project is a release branch (the
    model used by Mercurial based projects), while a list restricts releases to
    the named branches.

    A build is only ever "production" at level 3. ``params`` provides ``level``
    and ``project``, plus ``head_ref`` for projects configured with a branch
    list.

    :return str: One of "production" or "staging".
    """

    if params["level"] == "3":
        branches = release_branches.get(params["project"])

        if branches is True:
            return "production"

        if isinstance(branches, list):
            match = re.match(r"refs/heads/(\S+)$", params["head_ref"])

            if match and match.group(1) in branches:
                return "production"

    return "staging"
