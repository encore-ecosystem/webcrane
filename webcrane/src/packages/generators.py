from webcrane import LENGTH_OF_PATH_IN_PBAR
from webcrane import PACKAGE_MAX_SIZE
from .packages import Package, FileChunk, PackageChunk
from pickle import dumps
from pathlib import Path
from typing import Optional
from tqdm import tqdm
from webcrane.src.filepath import chunk_reader
from webcrane.src.tui import pretty_pbar


def file_generator(root: Path, relative_to_project: str, pbar: Optional[tqdm] = None):
    for chunk_index, data in enumerate(chunk_reader(root / relative_to_project)):
        pbar and pbar.set_description_str(desc=pretty_pbar(chunk_index, relative_to_project))
        yield FileChunk(data, relative_to_project)


def package_chunk_generator(package: Package):
    pickled_package = dumps(PackageChunk(package))
    data = pickled_package[:PACKAGE_MAX_SIZE]
    shift = 0
    while data:
        yield data
        shift += PACKAGE_MAX_SIZE
        data = pickled_package[shift: shift + PACKAGE_MAX_SIZE]


__all__ = [
    'package_chunk_generator',
    'file_generator',
]
