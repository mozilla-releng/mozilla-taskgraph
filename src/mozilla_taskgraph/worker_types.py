import binascii
from base64 import b64decode
from typing import Literal, Optional, Union

from taskgraph.transforms.task import payload_builder
from taskgraph.util.schema import Schema, taskref_or_string_msgspec

from mozilla_taskgraph.util.signed_artifacts import get_signed_artifacts

# -- scriptworker-bitrise schemas --


class BitriseConfig(
    Schema, rename=lambda name: name, forbid_unknown_fields=False, kw_only=True
):
    # Name of Bitrise App to schedule workflows on.
    app: str
    # List of workflows to trigger on specified app.
    # Can also be an object that maps workflow_ids to environment variables.
    workflows: list[Union[str, dict[str, list[dict[str, taskref_or_string_msgspec]]]]]
    # Directory prefix to store artifacts. Set this to 'public'
    # to create public artifacts.
    artifact_prefix: Optional[str] = None


class ScriptworkerBitriseSchema(Schema, forbid_unknown_fields=False, kw_only=True):
    bitrise: BitriseConfig


@payload_builder(
    "scriptworker-bitrise",
    schema=ScriptworkerBitriseSchema,
)
def build_bitrise_payload(config, task, task_def):
    bitrise = task["worker"]["bitrise"]
    task_def["tags"]["worker-implementation"] = "scriptworker"

    # Normalize environment variables to bitrise's format.
    workflow_permutations = {}
    for workflow in bitrise["workflows"]:
        if isinstance(workflow, str):
            # Empty environments
            continue
        for workflow_id, env_permutations in workflow.items():
            workflow_permutations.setdefault(workflow_id, [])
            for envs in env_permutations:
                workflow_permutations[workflow_id].append(
                    {
                        "environments": [
                            {"mapped_to": k, "value": v} for k, v in envs.items()
                        ]
                    }
                )

    def get_workflow_ids():
        ids = []
        for w in bitrise["workflows"]:
            if isinstance(w, str):
                ids.append(w)
            else:
                ids.extend(w.keys())
        ids = list(set(ids))  # Unique only
        ids.sort()  # sorted to allow for proper unit testing
        return ids

    scope_prefix = config.graph_config["scriptworker"]["scope-prefix"]
    scopes = task_def.setdefault("scopes", [])
    scopes.append(f"{scope_prefix}:bitrise:app:{bitrise['app']}")
    scopes.extend(
        [f"{scope_prefix}:bitrise:workflow:{wf}" for wf in get_workflow_ids()]
    )

    def normref(ref, type="heads"):
        if ref:
            prefix = f"refs/{type}/"
            if ref.startswith(prefix):
                return ref[len(prefix) :]
            # The ref is a different type than the requested one, return None
            # to indicate this.
            elif ref.startswith("refs/"):
                return None
        return ref

    # Set some global_params implicitly from Taskcluster params.
    global_params = {
        "commit_hash": config.params["head_rev"],
        "branch_repo_owner": config.params["head_repository"],
    }

    if head_ref := normref(config.params["head_ref"]):
        global_params["branch"] = head_ref

    if head_tag := normref(config.params["head_tag"], type="tags"):
        global_params["tag"] = head_tag

    if commit_message := config.params.get("commit_message"):
        global_params["commit_message"] = commit_message

    if pull_request_number := config.params.get("pull_request_number"):
        global_params["pull_request_id"] = pull_request_number

    if config.params["tasks_for"] == "github-pull-request":
        global_params["pull_request_author"] = config.params["owner"]

        if base_ref := normref(config.params["base_ref"]):
            global_params["branch_dest"] = base_ref

        if base_repository := config.params["base_repository"]:
            global_params["branch_dest_repo_owner"] = base_repository

    task_def["payload"] = {"global_params": global_params}
    if workflow_permutations:
        task_def["payload"]["workflow_params"] = workflow_permutations

    if bitrise.get("artifact_prefix"):
        task_def["payload"]["artifact_prefix"] = bitrise["artifact_prefix"]


# -- scriptworker-shipit schemas --


class ScriptworkerShipitSchema(Schema, forbid_unknown_fields=False, kw_only=True):
    release_name: str


@payload_builder(
    "scriptworker-shipit",
    schema=ScriptworkerShipitSchema,
)
def build_shipit_payload(config, task, task_def):
    worker = task["worker"]
    task_def["tags"]["worker-implementation"] = "scriptworker"
    task_def["payload"] = {"release_name": worker["release-name"]}


# -- scriptworker-signing schemas --


class SigningUpstreamArtifact(
    Schema, rename=lambda name: name, forbid_unknown_fields=False, kw_only=True
):
    # taskId of the task with the artifact
    taskId: taskref_or_string_msgspec
    # type of signing task (for CoT)
    taskType: str
    # Paths to the artifacts to sign
    paths: list[str]
    # Signing formats to use on each of the paths
    formats: list[str]
    # Only For MSI, optional for the signed Installer
    authenticode_comment: Optional[str] = None


class ScriptworkerSigningSchema(Schema, forbid_unknown_fields=False, kw_only=True):
    signing_type: str
    # list of artifact URLs for the artifacts that should be signed
    upstream_artifacts: list[SigningUpstreamArtifact]
    max_run_time: Optional[int] = None


@payload_builder(
    "scriptworker-signing",
    schema=ScriptworkerSigningSchema,
)
def build_signing_payload(config, task, task_def):
    worker = task["worker"]

    task_def["payload"] = {
        "upstreamArtifacts": worker["upstream-artifacts"],
    }
    if "max-run-time" in worker:
        task_def["payload"]["maxRunTime"] = worker["max-run-time"]

    task_def.setdefault("tags", {})["worker-implementation"] = "scriptworker"

    formats = set()
    for artifacts in worker["upstream-artifacts"]:
        formats.update(artifacts["formats"])

    scope_prefix = config.graph_config["scriptworker"]["scope-prefix"]
    scopes = set(task_def.get("scopes", []))
    scopes.add(f"{scope_prefix}:signing:cert:{worker['signing-type']}")

    task_def["scopes"] = sorted(scopes)

    # Set release artifacts
    artifacts = set(task.setdefault("attributes", {}).get("release_artifacts", []))
    for upstream_artifact in worker["upstream-artifacts"]:
        for path in upstream_artifact["paths"]:
            artifacts.update(
                get_signed_artifacts(
                    input=path,
                    formats=upstream_artifact["formats"],
                )
            )
    task["attributes"]["release_artifacts"] = sorted(list(artifacts))


# -- scriptworker-lando schemas --


class TomlInfoSync(Schema):
    toml_path: str


class AndroidL10nSyncConfig(Schema):
    from_branch: str
    toml_info: list[TomlInfoSync]


class TomlInfoImport(Schema):
    toml_path: str
    dest_path: str


class AndroidL10nImportConfig(Schema):
    from_repo_url: str
    toml_info: list[TomlInfoImport]


class PlatformConfig(Schema):
    platforms: list[str]
    path: str
    format: Optional[str] = None


class L10nBumpInfo(Schema):
    name: str
    path: str
    l10n_repo_url: str
    l10n_repo_target_branch: str
    platform_configs: list[PlatformConfig]
    ignore_config: Optional[object] = None


class TagConfig(Schema):
    types: list[Literal["buildN", "release"]]
    hg_repo_url: str


class VersionBumpConfig(Schema):
    bump_files: list[str]


class VersionFileStrict(Schema):
    filename: str
    version_bump: str
    new_suffix: Optional[str] = None


class VersionFile(Schema):
    filename: str
    version_bump: Optional[str] = None
    new_suffix: Optional[str] = None


# the remaining action types all end up using the "merge_day"
# landoscript action. however, these are quite varied tasks,
# and separating them out allows us to have stronger schemas.


class EsrBumpConfig(Schema):
    to_branch: str
    fetch_version_from: str
    version_files: list[VersionFileStrict]


class MainBumpConfig(Schema):
    to_branch: str
    fetch_version_from: str
    version_files: list[VersionFileStrict]
    replacements: Optional[list[list[str]]] = None
    regex_replacements: Optional[list[list[str]]] = None
    end_tag: Optional[str] = None


class EarlyToLateBetaConfig(Schema):
    to_branch: str
    # technically not used, but passing it keeps landoscript
    # code cleaner, so we may as well require a real value
    # for it.
    fetch_version_from: str
    replacements: Optional[list[list[str]]] = None


class UpliftConfig(Schema):
    fetch_version_from: str
    version_files: list[VersionFile]
    from_branch: str
    to_branch: str
    replacements: Optional[list[list[str]]] = None
    base_tag: Optional[str] = None
    end_tag: Optional[str] = None
    l10n_bump_info: Optional[list[L10nBumpInfo]] = None


class LandoAction(Schema, forbid_unknown_fields=False, kw_only=True):
    android_l10n_sync: Optional[AndroidL10nSyncConfig] = None
    android_l10n_import: Optional[AndroidL10nImportConfig] = None
    l10n_bump: Optional[list[L10nBumpInfo]] = None
    tag: Optional[TagConfig] = None
    version_bump: Optional[VersionBumpConfig] = None
    esr_bump: Optional[EsrBumpConfig] = None
    main_bump: Optional[MainBumpConfig] = None
    early_to_late_beta: Optional[EarlyToLateBetaConfig] = None
    uplift: Optional[UpliftConfig] = None


class ScriptworkerLandoSchema(Schema, forbid_unknown_fields=False, kw_only=True):
    lando_repo: str
    actions: list[LandoAction]
    ignore_closed_tree: Optional[bool] = None
    dontbuild: Optional[bool] = None
    force_dry_run: Optional[bool] = None
    matrix_rooms: Optional[list[str]] = None


@payload_builder(
    "scriptworker-lando",
    schema=ScriptworkerLandoSchema,
)
def build_lando_payload(config, task, task_def):
    worker = task["worker"]
    release_config = get_release_config(config)
    task_def["payload"] = {"actions": [], "lando_repo": worker["lando-repo"]}
    task_def["tags"]["worker-implementation"] = "scriptworker"
    actions = task_def["payload"]["actions"]

    if worker.get("ignore-closed-tree") is not None:
        task_def["payload"]["ignore_closed_tree"] = worker["ignore-closed-tree"]

    if worker.get("dontbuild"):
        task_def["payload"]["dontbuild"] = True

    if worker.get("force-dry-run"):
        task_def["payload"]["dry_run"] = True

    for action in worker["actions"]:
        if info := action.get("android-l10n-import"):
            android_l10n_import_info = dash_to_underscore(info)
            android_l10n_import_info["toml_info"] = [
                dash_to_underscore(ti) for ti in android_l10n_import_info["toml_info"]
            ]
            task_def["payload"]["android_l10n_import_info"] = android_l10n_import_info
            actions.append("android_l10n_import")

        if info := action.get("android-l10n-sync"):
            android_l10n_sync_info = dash_to_underscore(info)
            android_l10n_sync_info["toml_info"] = [
                dash_to_underscore(ti) for ti in android_l10n_sync_info["toml_info"]
            ]
            task_def["payload"]["android_l10n_sync_info"] = android_l10n_sync_info
            actions.append("android_l10n_sync")

        if info := action.get("l10n-bump"):
            task_def["payload"]["l10n_bump_info"] = process_l10n_bump_info(info)
            actions.append("l10n_bump")

        if info := action.get("tag"):
            tag_types = info["types"]
            tag_names = []
            product = task["shipping-product"].upper()
            version = release_config["version"].replace(".", "_")
            buildnum = release_config["build_number"]
            if "buildN" in tag_types:
                tag_names.extend(
                    [
                        f"{product}_{version}_BUILD{buildnum}",
                    ]
                )
            if "release" in tag_types:
                tag_names.extend([f"{product}_{version}_RELEASE"])
            tag_info = {
                "tags": tag_names,
                "hg_repo_url": info["hg-repo-url"],
                "revision": config.params[
                    "{}head_rev".format(worker.get("repo-param-prefix", ""))
                ],
            }
            task_def["payload"]["tag_info"] = tag_info
            actions.append("tag")

        if info := action.get("version-bump"):
            bump_info = {}
            bump_info["next_version"] = release_config["next_version"]
            bump_info["files"] = info["bump-files"]
            task_def["payload"]["version_bump_info"] = bump_info
            actions.append("version_bump")

        if info := action.get("esr-bump"):
            merge_info = dash_to_underscore(info)
            merge_info["version_files"] = [
                dash_to_underscore(vf) for vf in info["version-files"]
            ]
            task_def["payload"]["merge_info"] = merge_info
            actions.append("merge_day")

        if info := action.get("main-bump"):
            merge_info = dash_to_underscore(info)

            merge_info["version_files"] = [
                dash_to_underscore(vf) for vf in info["version-files"]
            ]
            task_def["payload"]["merge_info"] = merge_info
            actions.append("merge_day")

        if info := action.get("early-to-late-beta"):
            task_def["payload"]["merge_info"] = dash_to_underscore(info)
            actions.append("merge_day")

        if info := action.get("uplift"):
            merge_info = dash_to_underscore(info)
            merge_info["merge_old_head"] = True

            merge_info["version_files"] = [
                dash_to_underscore(vf) for vf in info["version-files"]
            ]
            if lbi := info.get("l10n-bump-info"):
                merge_info["l10n_bump_info"] = process_l10n_bump_info(lbi)

            task_def["payload"]["merge_info"] = merge_info
            actions.append("merge_day")

    scopes = set(task_def.get("scopes", []))
    scopes.add(f"project:releng:lando:repo:{worker['lando-repo']}")
    scopes.update([f"project:releng:lando:action:{action}" for action in actions])

    for matrix_room in worker.get("matrix-rooms", []):
        task_def.setdefault("routes", [])
        task_def["routes"].append(f"notify.matrix-room.{matrix_room}.on-pending")
        task_def["routes"].append(f"notify.matrix-room.{matrix_room}.on-resolved")
        scopes.add("queue:route:notify.matrix-room.*")

    task_def["scopes"] = sorted(scopes)


def get_release_config(config):
    """Get the build number and version for a release task.

    Currently only applies to beetmover tasks.

    Args:
        config (TransformConfig): The configuration for the kind being transformed.

    Returns:
        dict: containing both `build_number` and `version`.  This can be used to
            update `task.payload`.
    """
    return {
        "version": config.params["version"],
        "appVersion": config.params["app_version"],
        "next_version": config.params["next_version"],
        "build_number": config.params["build_number"],
    }


def process_l10n_bump_info(info):
    l10n_bump_info = []
    l10n_repo_urls = set()
    for lbi in info:
        l10n_repo_urls.add(lbi["l10n-repo-url"])
        l10n_bump_info.append(dash_to_underscore(lbi))

    if len(l10n_repo_urls) > 1:
        raise Exception(
            "Must use the same l10n-repo-url for all files in the same task!"
        )

    return l10n_bump_info


def dash_to_underscore(obj):
    new_obj = {}
    for k, v in obj.items():
        new_obj[k.replace("-", "_")] = v
    return new_obj


# -- scriptworker-beetmover-data schemas --


class DataMapEntry(Schema):
    data: str
    content_type: str
    destinations: list[taskref_or_string_msgspec]


class ScriptworkerBeetmoverDataSchema(
    Schema, forbid_unknown_fields=False, kw_only=True
):
    app_name: str
    bucket: str
    project: str
    data_map: list[DataMapEntry]
    dry_run: Optional[bool] = None


@payload_builder(
    "scriptworker-beetmover-data",
    schema=ScriptworkerBeetmoverDataSchema,
)
def build_beetmover_data_payload(_, task, task_def):
    worker = task["worker"]
    task_def["tags"]["worker-implementation"] = "scriptworker"

    task_def["payload"] = {
        "releaseProperties": {
            "appName": worker["app-name"],
        },
        "dataMap": [],
    }

    for dataMap in worker["data-map"]:
        data = dataMap["data"]
        try:
            b64decode(data)
        except binascii.Error:
            raise Exception(f"data must be base64 encoded! data was: {data}")

        task_def["payload"]["dataMap"].append(
            {
                "data": data,
                "contentType": dataMap["content-type"],
                "destinations": dataMap["destinations"],
            }
        )

    scopes = task_def.setdefault("scopes", [])
    scopes.extend(
        [
            f"project:{worker['project']}:releng:beetmover:bucket:{worker['bucket']}",
            f"project:{worker['project']}:releng:beetmover:action:upload-data",
        ]
    )
