from textwrap import dedent
from typing import Optional

from taskgraph import config as tg
from taskgraph.util.schema import Schema


class ShipitConfig(Schema, forbid_unknown_fields=False, kw_only=True):
    product: Optional[str] = None
    release_format: Optional[str] = None
    scope_prefix: Optional[str] = None


if isinstance(tg.graph_config_schema, type) and issubclass(
    tg.graph_config_schema, Schema
):
    # New msgspec-based graph_config_schema (upstream or no downstream override).

    class MozillaGraphConfigSchema(tg.graph_config_schema):
        """Extends the upstream GraphConfigSchema with Mozilla-specific fields."""

        # Ship It integration settings.
        shipit: Optional[ShipitConfig] = None
        # Python path of the form ``<module>:<obj>`` pointing to a function
        # that takes a set of parameters as input and returns the version
        # string to use for release tasks.
        # Defaults to ``mozilla_taskgraph.version:default_parser``.
        version_parser: Optional[str] = None

else:
    # Legacy voluptuous-based graph_config_schema (e.g. gecko_taskgraph override).
    from voluptuous import Optional as Vol_Optional

    MozillaGraphConfigSchema = tg.graph_config_schema.extend(
        {
            Vol_Optional("shipit"): {
                Vol_Optional("product"): str,
                Vol_Optional("release-format"): str,
                Vol_Optional("scope-prefix"): str,
            },
            Vol_Optional(
                "version-parser",
                description=dedent("""
                    Python path of the form ``<module>:<obj>`` pointing to a
                    function that takes a set of parameters as input and returns
                    the version string to use for release tasks.

                    Defaults to ``mozilla_taskgraph.version:default_parser``.
                    """.lstrip()),
            ): str,
        }
    )

tg.graph_config_schema = MozillaGraphConfigSchema
