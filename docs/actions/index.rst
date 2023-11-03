Actions
=======

The ``mozilla-taskgraph`` package provides a series of pre-defined actions that
can be enabled on a repository.

The provided actions are:

.. toctree::
   :maxdepth: 1

   release-promotion

Enabling Actions
----------------

None of the actions are enabled by default, consumers must explicitly opt in to
the actions they want with the :func:`~mozilla_taskgraph.actions.enable_action`
function. This is typically called from the
:func:`~taskgraph.config.GraphConfig.register` function.

For example:

.. code-block:: python

   from mozilla_taskgraph.actions import enable_action

   def register(graph_config):
       enable_action("release-promotion")

``mozilla-taskgraph`` provides default values for the action that should work
out of the box. But if desired, the action settings can be overridden with the
keyword args:

.. code-block:: python

   from mozilla_taskgraph.actions import enable_action

   def is_available(params):
      ...

   def register(graph_config):
       enable_action("release-promotion", available=is_available)
