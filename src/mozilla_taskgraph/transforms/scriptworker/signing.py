# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import re

from taskgraph.transforms.base import TransformSequence
from taskgraph.util.schema import (
    Schema,
    optionally_keyed_by,
    resolve_keyed_by,
)
from voluptuous import ALLOW_EXTRA, Any, Optional, Required

SIGNING_FORMATS = ["autograph_gpg"]
SIGNING_TYPES = ["dep", "release"]
DETACHED_SIGNATURE_EXTENSION = ".asc"

signing_schema = Schema(
    {
        Required("attributes"): {
            Optional("artifacts"): dict,
            Required("build-type"): str,
        },
        Required("signing"): optionally_keyed_by(
            "build-type",
            "level",
            {
                Required("format"): optionally_keyed_by(
                    "build-type", "level", Any(*SIGNING_FORMATS)
                ),
                Optional("type"): optionally_keyed_by(
                    "build-type", "level", Any(*SIGNING_TYPES)
                ),
                Optional("ignore-artifacts"): list,
            },
        ),
        Required("worker"): {
            Required("upstream-artifacts"): [
                {
                    # Paths to the artifacts to sign
                    Required("paths"): [str],
                }
            ],
        },
    },
    extra=ALLOW_EXTRA,
)

transforms = TransformSequence()
transforms.add_validate(signing_schema)


@transforms.add
def resolve_signing_keys(config, tasks):
    for task in tasks:
        for key in (
            "signing",
            "signing.format",
            "signing.type",
        ):
            resolve_keyed_by(
                task,
                key,
                item_name=task["name"],
                **{
                    "build-type": task["attributes"]["build-type"],
                    "level": config.params["level"],
                },
            )
        yield task


@transforms.add
def set_signing_attributes(_, tasks):
    for task in tasks:
        task["attributes"]["signed"] = True
        yield task


@transforms.add
def set_signing_format(_, tasks):
    for task in tasks:
        for upstream_artifact in task["worker"]["upstream-artifacts"]:
            upstream_artifact["formats"] = [task["signing"]["format"]]
        yield task


@transforms.add
def set_signing_and_worker_type(config, tasks):
    for task in tasks:
        signing_type = task["signing"].get("type")
        if not signing_type:
            signing_type = "release" if config.params["level"] == "3" else "dep"

        task.setdefault("worker", {})["signing-type"] = f"{signing_type}-signing"

        if "worker-type" not in task:
            worker_type = "signing"
            build_type = task["attributes"]["build-type"]

            if signing_type == "dep":
                worker_type = f"dep-{worker_type}"
            if build_type == "macos":
                worker_type = f"{build_type}-{worker_type}"
            task["worker-type"] = worker_type

        yield task


@transforms.add
def filter_out_ignored_artifacts(_, tasks):
    for task in tasks:
        ignore = task["signing"].get("ignore-artifacts")
        if not ignore:
            yield task
            continue

        def is_ignored(artifact):
            return not any(re.search(i, artifact) for i in ignore)

        if task["attributes"].get("artifacts"):
            task["attributes"]["artifacts"] = {
                extension: path
                for extension, path in task["attributes"]["artifacts"].items()
                if is_ignored(path)
            }

        for upstream_artifact in task["worker"]["upstream-artifacts"]:
            upstream_artifact["paths"] = [
                path for path in upstream_artifact["paths"] if is_ignored(path)
            ]

        yield task


@transforms.add
def set_gpg_detached_signature_artifacts(_, tasks):
    for task in tasks:
        if task["signing"]["format"] != "autograph_gpg":
            yield task
            continue

        task["attributes"]["artifacts"] = {
            extension
            + DETACHED_SIGNATURE_EXTENSION: path
            + DETACHED_SIGNATURE_EXTENSION
            for extension, path in task["attributes"]["artifacts"].items()
        }

        yield task


@transforms.add
def remove_signing_config(_, tasks):
    for task in tasks:
        del task["signing"]
        yield task
