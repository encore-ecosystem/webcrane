from webcrane.src.datastructures import DotIgnore
from pathlib import Path
import os


def walktree(root: Path, dot_ignore: DotIgnore, shift: int = 0) -> list[Path]:
    if dot_ignore.is_ignored(root):
        return []

    if root.is_dir():
        for path in os.listdir(root):
            path = root / path
            path_rel_to_proj = make_path_shorter(path, shift + 1)
            if dot_ignore.is_ignored(path_rel_to_proj):
                continue
            yield from walktree(path, dot_ignore, shift + 1)

    elif root.is_file():
        yield make_path_shorter(root, shift)

    else:
        raise TypeError(f"Unexpected file in {root}")


def make_path_shorter(root: Path, shift: int = 0) -> Path:
    return Path(*root.parts[-shift:])


__all__ = [
    'walktree'
]
