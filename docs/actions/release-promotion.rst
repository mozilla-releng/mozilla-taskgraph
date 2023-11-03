Release Promotion
=================

The release promotion action is used to schedule `release promotion phases`_.
That is, groups of tasks that are involved in a product's release.

This action is commonly invoked via the `Shipit interface`_, but can be
triggered manually through Taskcluster or Treeherder as well.

Configuration
-------------

This action can be configured via the ``release-promotion`` section of the
``taskcluster/ci/config.yml`` file. For example:

.. code-block:: yaml

   release-promotion:
     flavors:
       promote:
         target-tasks-method: promote
       ship:
         target-tasks-method: ship

The following options are supported:

* ``flavors`` - The set of valid release promotion flavors to perform.
  Typically there are either two flavors called ``promote`` and ``ship``, or
  three flavors called ``build``, ``promote`` and ``ship``. The latter is used
  if the builds produced on a normal push are not suitable for releasing. The
  values of these keys are objects that override parameters. It's common to
  create a ``target-tasks-method`` for each promotion flavor and pass it as a
  parameter here.
* ``rebuild-kinds`` - A list of kinds that should be re-built even if they
  exist in ``existing_tasks`` parameter. It's recommended to add
  ``cached_tasks`` to this list as they will be optimized anyway, and otherwise
  an expired cached task can cause a release to start over.

Input Schema
------------

The following inputs are allowed:

* ``release_promotion_flavor`` (str) - The flavor to run.
* ``do_not_optimize`` (List[str]) - The specified tasks will not be optimized
   (optional).
* ``rebuild_kinds`` (List[str]) - A list of kinds to rebuild. Overrides the
   default value in ``config.yml`` (optional).
* ``previous_graph_ids`` (List[str]) - A list of previous graphs to find
   existing tasks in. This should typically include the "on-push" graph and any
   previous release promotion phases (optional).

.. _release promotion phases: https://firefox-source-docs.mozilla.org/taskcluster/release-promotion.html
.. _Shipit interface: https://shipit.mozilla-releng.net/
