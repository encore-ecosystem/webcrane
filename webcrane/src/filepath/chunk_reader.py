from pathlib import Path
from typing import Optional, Iterable
import webcrane


def chunk_reader(filepath: Path, size: Optional[int] = None) -> Iterable[bytes]:
    size = size if size else webcrane.PACKAGE_MAX_SIZE
    with open(filepath, "rb") as f:
        to_ret = f.read(size)
        while to_ret:
            yield to_ret
            to_ret = f.read(size)


__all__ = ["chunk_reader"]
