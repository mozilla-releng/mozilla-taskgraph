# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from taskgraph.target_tasks import register_target_task


@register_target_task("ship-target-tasks")
def ship_target_tasks(full_task_graph, parameters, graph_config):
    def filter(task):
        if task.attributes.get("shipping-phase") == parameters["shipping_phase"]:
            return True

    return [label for label, task in full_task_graph.tasks.items() if filter(task)]
