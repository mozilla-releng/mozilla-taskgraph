# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import re


def release_level(params):
    """Whether this is a production release or not.

    The set of branches considered "production" is project specific and comes
    from the ``release_branches`` parameter, which is resolved at decision time
    from the graph config's ``release-branches`` mapping. A value of ``True``
    means every branch of the project is a release branch (the model used by
    Mercurial based projects), while a list restricts releases to the named
    branches.

    :return str: One of "production" or "staging".
    """
    if params["level"] != "3":
        return "staging"

    branches = params.get("release_branches")
    if not branches:
        return "staging"

    if branches is True:
        return "production"

    m = re.match(r"refs/heads/(\S+)$", params["head_ref"])
    if m is not None and m.group(1) in branches:
        return "production"

    return "staging"
