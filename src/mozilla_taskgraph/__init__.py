# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from importlib import import_module

from taskgraph.config import validate_graph_config


def register(graph_config):
    # Import modules to register decorated functions
    _import_modules(
        [
            "config",
            "worker_types",
        ]
    )
    validate_graph_config(graph_config._config)


def _import_modules(modules):
    for module in modules:
        import_module(f".{module}", package=__name__)
