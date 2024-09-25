from pathlib import Path

from hatchling.metadata.plugin.interface import MetadataHookInterface


class MetaDataHook(MetadataHookInterface):
    def update(self, metadata):
        metadata["version"] = Path(self.root).joinpath("version.txt").read_text()
