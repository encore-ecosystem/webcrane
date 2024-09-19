from pathlib import Path
from globmatch import glob_match


class DotIgnore:
    def __init__(self):
        self.patterns = set()

    def initialize(self, ignore_file_paths: list[Path]) -> 'DotIgnore':
        for ignore_file_path in ignore_file_paths:
            with open(ignore_file_path, "r") as f:
                for line in f.readlines():
                    # step 1: remove comments
                    pattern_ = line.split('#')[0].strip()
                    # step 2: add to ignore paths
                    self.patterns.add(pattern_)

        return self

    def add(self, path: str) -> None:
        if len(path) != 0:
            self.patterns.add(path)

    def optimize(self) -> 'DotIgnore':
        return self

    def is_ignored(self, path: Path) -> bool:
        return glob_match(path, self.patterns)


__all__ = [
    'DotIgnore'
]


# ===========
# unit test
# ===========
if __name__ == '__main__':
    dotignore = DotIgnore()

    patterns = [
        'wsvcs/*',
        'test_folder/waste.txt',
        'test_folder_2/*/folder_a',
    ]

    proj_structure = [
        Path('wsvcs') / '.wsvcsignore',
        Path('wsvcs') / 'manifest.toml',

        Path('test_folder') / 'waste.txt',
        Path('test_folder') / 'useful.txt',

        Path('test_folder_2') / 'hidden_path_1' / 'folder_a',
        Path('test_folder_2') / 'hidden_path_2' / 'folder_a',
        Path('test_folder_2') / 'hidden_path_3' / 'folder_b',
    ]

    for pattern in patterns:
        dotignore.add(pattern)

    for path in proj_structure:
        ignored = dotignore.is_ignored(path)
        print(f'{path}: {ignored}')
