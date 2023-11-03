Mozilla Taskgraph
=================

Mozilla Taskgraph is a companion library to `Taskgraph`_, the tool for
generating graphs of tasks for the `Taskcluster`_  task execution framework.

It contains logic that can be shared across all of Mozilla's projects using
the `Firefox CI Taskcluster instance`_.

.. _Taskgraph: https://taskcluster-taskgraph.readthedocs.io/
.. _Taskcluster: https://taskcluster.net/

Installation
------------

This project is only relevant to Mozilla's CI system, specifically the `Firefox
CI Taskcluster instance`_. Ensure your project is already using Taskgraph on
this instance before proceeding to install ``mozilla-taskgraph``.

The ``mozilla-taskgraph`` package should be installed alongside Taskgraph, using
the same method used to install the ``taskcluster-taskgraph`` package. If you
followed the `recommended way to bootstrap Taskgraph`_, simply add
``taskcluster-taskgraph`` to your ``taskcluster/requirements.in`` file:

.. code-block::

   taskcluster-taskgraph
   mozilla-taskgraph

Then regenerate the lockfile:

.. code-block:: bash

   cd taskcluster
   pip-compile requirements.in --generate-hashes

.. _Firefox CI Taskcluster instance: https://firefox-ci-tc.services.mozilla.com/
.. _recommended way to bootstrap Taskgraph: https://taskcluster-taskgraph.readthedocs.io/en/latest/howto/bootstrap-taskgraph.html

Usage
-----

Once installed, you can start to use the transforms and utilities that ``mozilla-taskgraph``
provides. For example, to use the ``release_artifacts`` transforms in your kind:

.. code-block:: yaml

   loader: taskgraph.loader.transform:loader

   transforms:
     - mozilla_taskgraph.transforms.scriptworker.release_artifacts
     ...

See `Taskgraph's documentation`_ for general information on using Taskgraph.

.. _Taskgraph's documentation: https://taskcluster-taskgraph.readthedocs.io


.. toctree::
   :hidden:
   :maxdepth: 3

   transforms/index
   actions/index
