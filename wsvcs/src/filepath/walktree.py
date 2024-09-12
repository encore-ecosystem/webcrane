from wsvcs.src.datastructures import DotIgnore
from pathlib import Path
import os


def walktree(root: Path, dot_ignore: DotIgnore, shift: int = 0) -> list[Path]:
    if dot_ignore.is_ignored(root):
        return []

    if root.is_dir():
        result = []
        for path in os.listdir(root):
            path = root / path
            if dot_ignore.is_ignored(path):
                continue
            result += walktree(path, dot_ignore, shift + 1)
        return result

    elif root.is_file():
        return [Path(*root.parts[-shift:])]

    else:
        raise TypeError(f"Unexpected file in {root}")


__all__ = [
    'walktree'
]
