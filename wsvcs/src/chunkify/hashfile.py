from wsvcs.src.chunkify.chunk_reader import read_in_chunks
from pathlib import Path
import hashlib


def hash_file(filepath: Path):
    filename = filepath.name.encode()

    hasher = hashlib.sha256(filename)
    with open(filepath, 'rb') as f:
        for chunk, _ in read_in_chunks(f):
            hasher.update(chunk)

    return hasher.hexdigest()[:8]
