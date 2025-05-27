from taskgraph.transforms.task import payload_builder, taskref_or_string
from voluptuous import Any, Extra, Optional, Required

from mozilla_taskgraph.util.signed_artifacts import get_signed_artifacts


@payload_builder(
    "scriptworker-bitrise",
    schema={
        Required("bitrise"): {
            Required(
                "app", description="Name of Bitrise App to schedule workflows on."
            ): str,
            Required(
                "workflows",
                description="List of workflows to trigger on specified app. "
                "Can also be an object that maps workflow_ids to environment variables.",
            ): [
                Any(
                    # Workflow id - no special environment variable
                    str,
                    # Map of workflow id to permutations of environment variables
                    {str: [{str: taskref_or_string}]},
                )
            ],
            Optional(
                "artifact_prefix",
                description="Directory prefix to store artifacts. Set this to 'public' "
                "to create public artifacts.",
            ): str,
        },
        Extra: object,
    },
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


@payload_builder(
    "scriptworker-shipit",
    schema={
        Required("release-name"): str,
    },
)
def build_shipit_payload(config, task, task_def):
    worker = task["worker"]
    task_def["tags"]["worker-implementation"] = "scriptworker"
    task_def["payload"] = {"release_name": worker["release-name"]}


@payload_builder(
    "scriptworker-signing",
    schema={
        Required("signing-type"): str,
        # list of artifact URLs for the artifacts that should be signed
        Required("upstream-artifacts"): [
            {
                # taskId of the task with the artifact
                Required("taskId"): taskref_or_string,
                # type of signing task (for CoT)
                Required("taskType"): str,
                # Paths to the artifacts to sign
                Required("paths"): [str],
                # Signing formats to use on each of the paths
                Required("formats"): [str],
                # Only For MSI, optional for the signed Installer
                Optional("authenticode_comment"): str,
            }
        ],
        Optional("max-run-time"): int,
    },
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


@payload_builder(
    "scriptworker-lando",
    schema={
        Required("lando-repo"): str,
        Optional("hg-repo-url"): str,
        Optional("ignore-closed-tree"): bool,
        Optional("dontbuild"): bool,
        Optional("tags"): [Any("buildN", "release", None)],
        Optional("force-dry-run"): bool,
        Optional("android-l10n-import-info"): {
            Required("from-repo-url"): str,
            Required("toml-info"): [
                {
                    Required("toml-path"): str,
                    Required("dest-path"): str,
                }
            ],
        },
        Optional("android-l10n-sync-info"): {
            Required("from-branch"): str,
            Required("toml-info"): [
                {
                    Required("toml-path"): str,
                }
            ],
        },
        Optional("l10n-bump-info"): [
            {
                Required("name"): str,
                Required("path"): str,
                Optional("l10n-repo-url"): str,
                Optional("l10n-repo-target-branch"): str,
                Optional("ignore-config"): object,
                Required("platform-configs"): [
                    {
                        Required("platforms"): [str],
                        Required("path"): str,
                        Optional("format"): str,
                    }
                ],
            }
        ],
        Optional("bump-files"): [str],
        Optional("merge-info"): object,
    },
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

    if worker.get("android-l10n-import-info"):
        android_l10n_import_info = {}
        for k, v in worker["android-l10n-import-info"].items():
            android_l10n_import_info[k.replace("-", "_")] = worker[
                "android-l10n-import-info"
            ][k]
        android_l10n_import_info["toml_info"] = [
            {
                param_name.replace("-", "_"): param_value
                for param_name, param_value in entry.items()
            }
            for entry in worker["android-l10n-import-info"]["toml-info"]
        ]
        task_def["payload"]["android_l10n_import_info"] = android_l10n_import_info
        actions.append("android_l10n_import")

    if worker.get("android-l10n-sync-info"):
        android_l10n_sync_info = {}
        for k, v in worker["android-l10n-sync-info"].items():
            android_l10n_sync_info[k.replace("-", "_")] = worker[
                "android-l10n-sync-info"
            ][k]
        android_l10n_sync_info["toml_info"] = [
            {
                param_name.replace("-", "_"): param_value
                for param_name, param_value in entry.items()
            }
            for entry in worker["android-l10n-sync-info"]["toml-info"]
        ]
        task_def["payload"]["android_l10n_sync_info"] = android_l10n_sync_info
        actions.append("android_l10n_sync")

    if worker.get("l10n-bump-info"):
        l10n_bump_info = []
        l10n_repo_urls = set()
        for lbi in worker["l10n-bump-info"]:
            new_lbi = {}
            if "l10n-repo-url" in lbi:
                l10n_repo_urls.add(lbi["l10n-repo-url"])
            for k, v in lbi.items():
                new_lbi[k.replace("-", "_")] = lbi[k]
            l10n_bump_info.append(new_lbi)

        task_def["payload"]["l10n_bump_info"] = l10n_bump_info
        if len(l10n_repo_urls) > 1:
            raise Exception(
                "Must use the same l10n-repo-url for all files in the same task!"
            )
        elif len(l10n_repo_urls) == 1:
            actions.append("l10n_bump")

    if worker.get("tags"):
        tag_names = []
        product = task["shipping-product"].upper()
        version = release_config["version"].replace(".", "_")
        buildnum = release_config["build_number"]
        if "buildN" in worker["tags"]:
            tag_names.extend(
                [
                    f"{product}_{version}_BUILD{buildnum}",
                ]
            )
        if "release" in worker["tags"]:
            tag_names.extend([f"{product}_{version}_RELEASE"])
        tag_info = {
            "tags": tag_names,
            "hg_repo_url": worker["hg-repo-url"],
            "revision": config.params[
                "{}head_rev".format(worker.get("repo-param-prefix", ""))
            ],
        }
        task_def["payload"]["tag_info"] = tag_info
        actions.append("tag")

    if worker.get("bump-files"):
        bump_info = {}
        bump_info["next_version"] = release_config["next_version"]
        bump_info["files"] = worker["bump-files"]
        task_def["payload"]["version_bump_info"] = bump_info
        actions.append("version_bump")

    if worker.get("merge-info"):
        merge_info = {
            merge_param_name.replace("-", "_"): merge_param_value
            for merge_param_name, merge_param_value in worker["merge-info"].items()
            if merge_param_name != "version-files"
        }
        merge_info["version_files"] = [
            {
                file_param_name.replace("-", "_"): file_param_value
                for file_param_name, file_param_value in file_entry.items()
            }
            for file_entry in worker["merge-info"]["version-files"]
        ]
        # hack alert: co-opt the l10n_bump_info into the merge_info section
        # this should be cleaned up to avoid l10n_bump_info ever existing
        # in the payload
        if task_def["payload"].get("l10n_bump_info"):
            actions.remove("l10n_bump")
            merge_info["l10n_bump_info"] = task_def["payload"].pop("l10n_bump_info")

        task_def["payload"]["merge_info"] = merge_info
        actions.append("merge_day")

    scopes = set(task_def.get("scopes", []))
    scopes.add(f"project:releng:lando:repo:{worker['lando-repo']}")
    scopes.update([f"project:releng:lando:action:{action}" for action in actions])
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
