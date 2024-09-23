from webcrane import LENGTH_OF_PATH_IN_PBAR
from webcrane import PACKAGE_MAX_SIZE
from .packages import Package, FileChunk, PackageChunk
from pickle import dumps
from pathlib import Path
from typing import Optional, Iterable, Generator
from tqdm import tqdm
from termcolor import colored
from webcrane.src.filepath import chunk_reader
import pickle


def file_generator(root: Path, relative_to_project: str, pbar: Optional[tqdm] = None):
    for chunk_index, data in enumerate(chunk_reader(root / relative_to_project)):
        if pbar:
            if len(relative_to_project) <= LENGTH_OF_PATH_IN_PBAR:
                desc = relative_to_project
            else:
                desc = '...' + relative_to_project[-LENGTH_OF_PATH_IN_PBAR + 3:]

            desc = f"[chunk: {chunk_index:>4}] Working on: {colored(desc, 'cyan')}"
            pbar.set_description_str(desc=f"{desc:>{LENGTH_OF_PATH_IN_PBAR}}")

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
    'package_chunk_generator',
    'file_generator',
]
