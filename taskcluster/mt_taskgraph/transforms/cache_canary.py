# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from taskgraph.transforms.base import TransformSequence


transforms = TransformSequence()


@transforms.add
def set_cache_canary_rank(config, tasks):
    for task in tasks:
        if task["label"] == "docker-image-python":
            task["task"].setdefault("extra", {}).setdefault("index", {})["rank"] = 2147483647
        yield task
