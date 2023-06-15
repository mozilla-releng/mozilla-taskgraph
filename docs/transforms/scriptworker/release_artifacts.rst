Release Artifacts
=================

Tasks can produce many different artifacts, but normally only a subset of them
are relevant to a release pipeline. For example, build tasks might produce
logs, debug information, as well as the build artifact itself. However, only
the build artifact will be consumed by downstream tasks for purposes of
generating a release.

The ``mozilla_taskgraph.transforms.scriptworker.release_artifacts`` transforms
provide a convenient mechanism for declaring artifacts that should be
associated with release activities.

Usage
-----

To use the ``release_artifacts`` transforms, first add it to your ``kind.yml``
file:

.. code-block:: yaml

   loader: taskgraph.loader.transform:loader

   transforms:
     - mozilla_taskgraph.transforms.scriptworker.release_artifacts

Then define a ``release-artifacts`` key in your task definition, either
directly in the ``kind.yml`` file, or in a transform function that runs before
``release_artifacts``. For example:

.. code-block:: yaml

   tasks:
     build:
       release-artifacts:
         - build.zip
         - build.zip.sha256

In the above example, the ``build`` task is declaring that it will produce a
``build.zip`` and a ``build.zip.sha256`` artifact, and that these artifacts
will be used by downstream release tasks. The task is responsible for actually
producing these artifacts in a pre-determined location. This location varies by
worker implementation:

* For ``generic-worker``, they must be created in an ``artifacts`` directory
  relative to the task's current working directory.
* For ``docker-worker``, the artifacts must be created in the absolute
  ``/builds/worker/artifacts`` directory.

Details
-------

The ``release_artifacts`` transforms will make two changes:

1. They'll convert the list of artifacts to the proper format expected by the
   worker.
2. They'll create a ``release-artifacts`` attribute which downstream release
   tasks can use to determine which artifacts to operate on.

So in the previous example, the ``build`` task would be transformed to something
like (assuming it uses ``generic-worker``):

.. code-block:: yaml

   build:
     attributes:
       release-artifacts:
         - type: file
           name: public/build/build.zip
           path: artifacts/build.zip
         - type: file
           name: public/build/build.zip.sha256
           path: artifacts/build.zip.sha256
     worker:
       artifacts:
         - type: file
           name: public/build/build.zip
           path: artifacts/build.zip
         - type: file
           name: public/build/build.zip.sha256
           path: artifacts/build.zip.sha256
