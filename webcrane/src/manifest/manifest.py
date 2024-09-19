from pathlib import Path
from typing import Optional
import tomllib
import tomli_w


class Manifest:
    def __init__(self):
        self.manifest = None

    def read_manifest(self, path_to_manifest: Path):
        if path_to_manifest.exists():
            with open(path_to_manifest, "rb") as f:
                self.manifest = tomllib.load(f)
        else:
            raise FileNotFoundError(path_to_manifest)

    def get_manifest(self) -> Optional[dict]:
        return self.manifest

    def save(self, save_path: Path):
        with open(save_path, "wb") as f:
            tomli_w.dump(self.manifest, f)

    def __setitem__(self, key, value):
        if self.manifest is None:
            raise ValueError("Manifest not initialized")

        self.manifest[key] = value

    def __getitem__(self, item):
        if self.manifest is None:
            raise KeyError("Manifest not initialized")

        return self.manifest[item]


__all__ = [
    'Manifest'
]
