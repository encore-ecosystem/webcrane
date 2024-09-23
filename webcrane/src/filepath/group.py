from webcrane.src.datastructures import Surjection, DotIgnore
from webcrane.src.filepath.hashfile import hash_file
from enum import Enum
import concurrent.futures
from pathlib import Path
from termcolor import colored
from webcrane.src.filepath import walktree
import tqdm


class GroupType(str, Enum):
    UPDATE = 'update'
    DELETE = 'delete'
    MOVE = 'move'
    SAVE = 'save'


def process_file(root_path: Path, short_path: Path):
    return str(short_path), hash_file(root_path / short_path)


def group_file(root: Path, short_path: Path, path_hash_sur: Surjection) -> tuple[GroupType, tuple]:
    short_path = str(short_path)
    long_path = root / short_path
    file_hash = hash_file(long_path)

    # case 1: files at the same directory
    if short_path in path_hash_sur:
        if path_hash_sur[short_path] == file_hash:
            # same file
            return GroupType.SAVE, (short_path, )
        else:
            # update
            print(f"{colored("[U]", "magenta")}: {short_path}")
            return GroupType.UPDATE, (short_path, )

    # case 2: same files at the difference folders
    elif file_hash in path_hash_sur:
        # move                 <from>         <to>
        return GroupType.MOVE, (short_path, path_hash_sur[file_hash])

    # case 3: waste file
    else:
        # waste
        return GroupType.DELETE, (short_path, )


def threaded_grouping(root: Path, dotignore: DotIgnore, path_hash_sur: Surjection, threads: int = 4)  -> tuple[set, set, set, set]:
    files_to_update = set()
    files_to_delete = set()
    files_to_move   = set()
    files_to_save   = set()

    with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
        future_to_group = {executor.submit(group_file, root, path, path_hash_sur): path for path in walktree(root, dotignore)}
        with tqdm.tqdm(concurrent.futures.as_completed(future_to_group), total=len(future_to_group)) as pbar:
            for future in pbar:
                group, extra = future.result()
                match group:
                    case GroupType.UPDATE:
                        files_to_update.add(extra[0])
                    case GroupType.DELETE:
                        files_to_delete.add(extra[0])
                    case GroupType.MOVE:
                        files_to_move.add(extra)
                    case GroupType.SAVE:
                        files_to_save.add(extra)

        # case 4: new files
        new_files = set(path_hash_sur.from_keys()).difference(files_to_save)

        return files_to_update, files_to_delete, files_to_move, new_files


__all__ = [
    'threaded_grouping'
]
