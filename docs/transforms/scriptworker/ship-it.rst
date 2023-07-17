Ship-It
=======

The transforms provided in this module are designed to interact with Release
Engineering's `Ship-It`_, a tool to help manage releases of Firefox and other
products.

Graph Configuration
-------------------

Configuration for Ship-It related transforms belong under a ``shipit`` section
in the ``graph_config`` (typically ``taskcluster/ci/config.yml``). At a minimum,
a ``product`` key is required:

.. code-block:: yaml

   shipit:
     product: my-product

There are also a few optional keys:

* ``release-format`` - A string that gets interpolated with the `product`,
  `version` and `build_number`. Defaults to
  ``{product}-{version}-build{build_number}``.
* ``scope-prefix`` - A string denoting a prefix used for all Ship-It related
  scopes for this product. Defaults to ``project:releng:ship-it``.

Transforms
----------

mark_as_shipped
~~~~~~~~~~~~~~~

The :mod:`~mozilla_taskgraph.transforms.scriptworker.shipit.mark_as_shipped`
transforms can be used to create a task that will mark a release as shipped in
Ship-It.

Typically such a task should use Taskgraph's `from_deps transforms`_ to depend
on all leaf nodes of a "ship graph". That way the release will only be marked
as shipped after all release tasks have completed successfully.

Other than having dependencies set up properly, no special configuration is
required in the task to use these transforms.

.. _Ship-It: https://github.com/mozilla-releng/shipit
.. _from_deps transforms: https://taskcluster-taskgraph.readthedocs.io/en/latest/reference/transforms/from_deps.html
