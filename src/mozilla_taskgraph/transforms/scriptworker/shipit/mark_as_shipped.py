# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os

from taskgraph.transforms.base import TransformSequence

transforms = TransformSequence()


@transforms.add
def make_task_description(config, tasks):
    if "shipit" not in config.graph_config:
        config_path = os.path.join(config.graph_config.root_dir, "config.yml")
        raise Exception(f"Missing 'shipit' config in {config_path}")

    shipit = config.graph_config["shipit"]
    release_format = shipit.get(
        "release-format", "{product}-{version}-build{build_number}"
    )
    scope_prefix = shipit.get("scope-prefix", "project:releng:ship-it")
    shipit_server = "production" if config.params["level"] == "3" else "staging"
    version = config.params.get("version", "<ver>")
    for task in tasks:
        task.setdefault("label", "mark-as-shipped")
        task["description"] = f"Mark {shipit['product']} as shipped in Ship-It"
        task["scopes"] = [
            f"{scope_prefix}:action:mark-as-shipped",
            f"{scope_prefix}:server:{shipit_server}",
        ]
        task.setdefault("worker", {})["release-name"] = release_format.format(
            product=shipit["product"],
            version=version,
            build_number=config.params.get("build_number", 1),
        )
        yield task
