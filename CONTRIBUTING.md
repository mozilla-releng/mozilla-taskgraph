Contributing to Mozilla Taskgraph
=================================

Thanks for your interest in mozilla-taskgraph! To participate in this community, please
review our [code of conduct].

[code of conduct]: https://github.com/mozilla-releng/mozilla-taskgraph/blob/main/CODE_OF_CONDUCT.md

Clone the Repo
--------------

To contribute to mozilla-taskgraph, you'll need to clone the repository:

```
# first fork mozilla-taskgraph
git clone https://github.com/<user>/mozilla-taskgraph
cd mozilla-taskgraph
git remote add upstream https://github.com/mozilla-releng/mozilla-taskgraph
```

Setting Up the Environment
--------------------------

We use a tool called [uv] to manage mozilla-taskgraph and its dependencies. First,
follow the [installation instructions].

Then run:

```
uv sync
```

This does several things:

1. Creates a virtualenv for the project in a `.venv` directory (if necessary).
2. Syncs the project's dependencies as pinned in `uv.lock` (if necessary).
3. Installs `mozilla-taskgraph` as an editable package (if necessary).

Now you can prefix commands with `uv run` and they'll have access to this
environment.

[uv]: https://docs.astral.sh/uv/
[installation instructions]: https://docs.astral.sh/uv/getting-started/installation/

Running Tests
-------------

Tests are run with the [pytest] framework:

```
uv run pytest
```

[pytest]: https://docs.pytest.org

Running Checks
--------------

Linters and formatters are run via [pre-commit]. To install the hooks, run:

```
pre-commit install -t pre-commit -t commit-msg
```

Now checks will automatically run on every commit. If you prefer to run checks
manually, you can use:

```
pre-commit run
```

Most of the checks we enforce are done with [ruff]. See
[pre-commit-config.yaml] for a full list of linters and formatters.

[pre-commit]: https://pre-commit.com/
[ruff]: https://docs.astral.sh/ruff/
[pre-commit-config.yaml]: https://github.com/mozilla-releng/mozilla-taskgraph/blob/main/.pre-commit-config.yaml

Releasing
---------

A tool called [commitizen] can optionally be used to assist with releasing
the package. First make sure it is installed.

Then create the version bump commit:

```
cz bump
git show
```

Verify the commit is what you expect, then create a pull request and get the
commit merged into `main`.

If you merge the pull request using the `squash` method, recreate the tag after
pulling to make sure it points to the same commit as the one on main.

Then, push your tag upstream:

```
git push upstream --tags
```

Finally, create a release in Github, choosing the tag that you just pushed.
This will trigger the `pypi-publish` workflow and upload the package to pypi.

[commitizen]: https://commitizen-tools.github.io/commitizen/
