from taskgraph.transforms.task import payload_builder, taskref_or_string
from voluptuous import Extra, Optional, Required


@payload_builder(
    "scriptworker-bitrise",
    schema={
        Required("bitrise"): {
            Required(
                "app", description="Name of Bitrise App to schedule workflows on."
            ): str,
            Required(
                "workflows",
                description="List of workflows to trigger on specified app.",
            ): [str],
            Optional(
                "env", description="Environment variables to pass into the build"
            ): {str: taskref_or_string},
            Optional(
                "build_params",
                description="Parameters describing the build context to pass "
                "onto Bitrise. All keys are optional but specific workflows "
                "may depend on particular keys being set.",
            ): {
                Optional(
                    "branch",
                    description="The branch running the build. For pull "
                    "requests, this should be the head branch.",
                ): str,
                Optional(
                    "branch_dest",
                    description="The destination branch where the branch "
                    "running the build will merge into. Only valid for pull "
                    "requests.",
                ): str,
                Optional(
                    "branch_dest_repo_owner",
                    description="The repository owning the destination branch. "
                    "Only valid for pull requests.",
                ): str,
                Optional(
                    "branch_repo_owner", description="The repository owning the branch."
                ): str,
                Optional(
                    "commit_hash",
                    description="The hash of the commit running the build.",
                ): str,
                Optional(
                    "commit_message",
                    description="The commit message of the commit running the build.",
                ): str,
                Optional(
                    "environments",
                    description="Environment variables to pass into the build.",
                ): [{Required("mapped_to"): str, Optional("value"): taskref_or_string}],
                Optional(
                    "pull_request_author",
                    description="The author of the pull request running the build.",
                ): str,
                Optional(
                    "pull_request_id",
                    description="The id of the pull request running the build.",
                ): int,
                Optional(
                    "skip_git_status_report",
                    description="Whether Bitrise should send a status report to "
                    "Github (default False).",
                ): bool,
                Optional(
                    "tag", description="The tag of the commit running the build."
                ): str,
            },
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
    build_params = bitrise.get("build_params") or {}
    task_def["tags"]["worker-implementation"] = "scriptworker"

    scope_prefix = config.graph_config["scriptworker"]["scope-prefix"]
    scopes = task_def.setdefault("scopes", [])
    scopes.append(f"{scope_prefix}:bitrise:app:{bitrise['app']}")
    scopes.extend(
        [f"{scope_prefix}:bitrise:workflow:{wf}" for wf in bitrise["workflows"]]
    )

    # Normalize environment variables to bitrise's format.
    env = bitrise.get("env", {})
    if env:
        build_params.setdefault("environments", [])
        for k, v in env.items():
            build_params["environments"].append({"mapped_to": k, "value": v})

    # Set some build_params implicitly from Taskcluster params.
    build_params.setdefault("commit_hash", config.params["head_rev"])
    build_params.setdefault("branch_repo_owner", config.params["head_repository"])

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

    head_ref = normref(config.params["head_ref"])
    head_tag = normref(config.params["head_tag"], type="tags")
    base_ref = normref(config.params["base_ref"])

    if head_ref:
        build_params.setdefault("branch", head_ref)

    if head_tag:
        build_params.setdefault("tag", head_tag)

    if config.params["tasks_for"] == "github-pull-request":
        build_params.setdefault("pull_request_author", config.params["owner"])

        if base_ref:
            build_params.setdefault("branch_dest", base_ref)

        if config.params["base_repository"]:
            build_params.setdefault(
                "branch_dest_repo_owner", config.params["base_repository"]
            )

    payload = task_def["payload"] = {"build_params": build_params}
    if bitrise.get("artifact_prefix"):
        payload["artifact_prefix"] = bitrise["artifact_prefix"]


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
