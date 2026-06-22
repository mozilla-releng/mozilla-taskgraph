# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from typing import Optional, Union

from taskgraph.parameters import extend_parameters_schema
from taskgraph.util.schema import Schema


class MozillaParametersSchema(Schema, kw_only=True):
    # Branches of the current project that are considered "production"
    # releases. Resolved from the graph config's `release-branches` mapping by
    # `set_release_branches`. `True` means all branches of the project are
    # release branches, a list restricts releases to the named branches, and
    # `None` means the project has no release branches.
    release_branches: Optional[Union[bool, list[str]]] = None


def get_defaults(repo_root=None):
    return {
        "release_branches": None,
    }


def register_parameters():
    extend_parameters_schema(MozillaParametersSchema, defaults_fn=get_defaults)


def set_release_branches(graph_config, parameters):
    """Resolve the current project's release branches from the graph config.

    Projects should call this from their `decision-parameters` function so that
    `release_branches` is persisted into `parameters.yml` and available to
    consumers that only have a `Parameters` object (e.g. action tasks).
    """
    mapping = graph_config._config.get("release-branches") or {}
    parameters["release_branches"] = mapping.get(parameters["project"])
