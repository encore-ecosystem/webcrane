from .chunk_reader import chunk_reader
from webcrane.src.packages import PackageHash
from typing import Generator
import concurrent.futures
from pathlib import Path
import hashlib
import tqdm

HASH_SIZE = 8


def process_file(root_path: Path, short_path: Path):
    return str(short_path), hash_file(root_path / short_path)


def hash_file(filepath: Path) -> str:
    filename = filepath.name.encode()

    hasher = hashlib.sha256(filename)
    for chunk in chunk_reader(filepath):
        hasher.update(chunk)

    return hasher.hexdigest()[:HASH_SIZE]


def threaded_hashing(root: Path, file_local_paths: list, threads: int = 4):
    with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
        future_to_path = {executor.submit(process_file, root, path): path for path in file_local_paths}
        for future in tqdm.tqdm(concurrent.futures.as_completed(future_to_path), total=len(file_local_paths)):
            path, file_hash = future.result()
            yield PackageHash(file_hash, path)
