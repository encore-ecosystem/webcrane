from pathlib import Path
import os


def walktree(root: Path, black_list: set, shift: int = 0) -> list[Path]:
    if root in black_list:
        return []

    if root.is_dir():
        result = []
        for path in os.listdir(root):
            if path in black_list:
                continue
            result += walktree(root / path, black_list, shift + 1)
        return result

    elif root.is_file():
        return [Path(*root.parts[-shift:])]

    else:
        raise TypeError(f"Unexpected file in {root}")


__all__ = [
    'walktree'
]
