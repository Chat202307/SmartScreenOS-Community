from __future__ import annotations

from pathlib import Path

import yaml

from .model import CapabilityManifest


class ManifestLoader:

    def load(self, filename: str | Path) -> CapabilityManifest:

        path = Path(filename)

        data = yaml.safe_load(path.read_text(encoding="utf-8"))

        return CapabilityManifest(
            manifest_version=data["manifestVersion"],
            capability_id=data["id"],
            name=data["name"],
            category=data["category"],
            version=data["version"],
            provider=data["provider"],
            description=data.get("description", ""),
            entry_point=data.get("entryPoint", ""),
            contracts=tuple(data.get("contracts", [])),
            required_dependencies=tuple(
                data.get("dependencies", {}).get("required", [])
            ),
            optional_dependencies=tuple(
                data.get("dependencies", {}).get("optional", [])
            ),
            configuration=data.get("configuration", {}),
        )
