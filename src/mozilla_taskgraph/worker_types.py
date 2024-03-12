from taskgraph.transforms.task import payload_builder
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
                ): dict,
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
        },
        Extra: object,
    },
)
def build_bitrise_payload(config, task, task_def):
    bitrise = task["worker"]["bitrise"]
    build_params = task_def["payload"] = bitrise.get("build_params") or {}
    task_def["tags"]["worker-implementation"] = "scriptworker"

    scope_prefix = config.graph_config["scriptworker"]["scope-prefix"]
    scopes = task_def.setdefault("scopes", [])
    scopes.append(f"{scope_prefix}:bitrise:app:{bitrise['app']}")
    scopes.extend(
        [f"{scope_prefix}:bitrise:workflow:{wf}" for wf in bitrise["workflows"]]
    )

    # Set some build_params implicitly from Taskcluster params.
    build_params.setdefault("commit_hash", config.params["head_rev"])
    build_params.setdefault("branch_repo_owner", config.params["head_repository"])

    if config.params["head_ref"]:
        build_params.setdefault("branch", config.params["head_ref"])

    if config.params["head_tag"]:
        build_params.setdefault("tag", config.params["head_tag"])

    if config.params["tasks_for"] == "github-pull-request":
        build_params.setdefault("pull_request_author", config.params["owner"])

        if config.params["base_ref"]:
            build_params.setdefault("branch_dest", config.params["base_ref"])

        if config.params["base_repository"]:
            build_params.setdefault(
                "branch_dest_repo_owner", config.params["base_repository"]
            )


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
