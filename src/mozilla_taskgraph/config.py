from taskgraph import config as tg
from voluptuous import Optional, Required

tg.graph_config_schema = tg.graph_config_schema.extend(
    {
        Optional("shipit"): {
            Required("product"): str,
            Optional("release-format"): str,
            Optional("scope-prefix"): str,
        },
    }
)
