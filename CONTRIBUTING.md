Contributing to Mozilla Taskgraph
=================================

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
commit merged into `main`. Once merged, push your tag upstream:

```
git push upstream --tags
```

Finally, create a release in Github, choosing the tag that you just pushed.
This will trigger the `pypi-publish` workflow and upload the package to pypi.

[commitizen]: https://commitizen-tools.github.io/commitizen/
