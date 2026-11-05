# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""
Product-neutral build-signing transforms.

These shape a signing task from its primary dependency: they derive the signing
index routes and turn a set of signing specs into the ``upstream-artifacts``
that the ``scriptworker-signing`` payload builder consumes.

The decision of *which* artifacts and formats to sign is product-specific (it
depends on platforms, locales, installer variants, ...), so it is NOT made
here. An earlier, project-specific transform is expected to populate
``task["signing-artifacts"]`` with a list of specs, each of the form::

    {"paths": ["<locale>/target.zip", ...], "formats": ["...", ...]}
"""

from collections.abc import Iterator
from typing import Optional

from taskgraph.transforms.base import TransformConfig, TransformSequence
from taskgraph.util.dependencies import get_primary_dependency
from taskgraph.util.schema import Schema

from mozilla_taskgraph.util.attributes import copy_attributes_from_dependent_job


class SigningArtifactSchema(Schema, kw_only=True):
    # Paths, relative to the dependency's artifact prefix, of the artifacts to sign.
    paths: list[str]
    # Signing formats to apply to each of those paths.
    formats: list[str]


class BuildSigningSchema(Schema, forbid_unknown_fields=False, kw_only=True):
    # Specs of the artifacts to sign. A project with nothing to sign for a given
    # task should say so explicitly with an empty list.
    signing_artifacts: list[SigningArtifactSchema]
    # Whether to mirror the dependency's index routes. Defaults to True.
    enable_signing_routes: Optional[bool] = None


transforms = TransformSequence()
transforms.add_validate(BuildSigningSchema)


@transforms.add
def add_signed_routes(config: TransformConfig, tasks: Iterator[dict]):
    """Mirror the primary dependency's index routes, inserting a ``signed``
    component after the project.

    Index routes follow taskgraph's ``index.<trust-domain>.v2.<project>...``
    layout, so the prefix is derived rather than configured. Deciding *which*
    tasks deserve signed routes is project policy: filter them out in an earlier
    transform, or set ``enable-signing-routes`` to False.
    """
    route_prefix = f"index.{config.graph_config['trust-domain']}.v2"

    for task in tasks:
        dep_task = get_primary_dependency(config, task)
        enable_signing_routes = task.pop("enable-signing-routes", True)

        task["routes"] = []
        if enable_signing_routes:
            for route in dep_task.task.get("routes", []):
                if not route.startswith(f"{route_prefix}."):
                    continue
                project, _, rest = route[len(route_prefix) + 1 :].partition(".")
                task["routes"].append(f"{route_prefix}.{project}.signed.{rest}")

        yield task


def _artifact_task_type(dep_kind):
    """Notarization dependencies run on scriptworker; everything else is a build."""
    return "scriptworker" if "notarization" in dep_kind else "build"


@transforms.add
def define_upstream_artifacts(config: TransformConfig, tasks: Iterator[dict]):
    """Copy the curated attributes from the primary dependency and shape the
    project-provided ``signing-artifacts`` specs into ``upstream-artifacts``."""
    for task in tasks:
        dep_task = get_primary_dependency(config, task)

        attributes = task.setdefault("attributes", {})
        attributes.update(copy_attributes_from_dependent_job(dep_task))
        attributes["signed"] = True

        specs = task.pop("signing-artifacts")
        task_ref = {"task-reference": f"<{dep_task.kind}>"}
        task_type = _artifact_task_type(dep_task.kind)

        task["upstream-artifacts"] = [
            {
                "taskId": task_ref,
                "taskType": task_type,
                "paths": spec["paths"],
                "formats": spec["formats"],
            }
            for spec in specs
        ]

        yield task
