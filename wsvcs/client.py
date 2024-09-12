from wsvcs.src.chunkify.chunk_reader import *
from wsvcs.src.filepath.walktree import walktree
from wsvcs.src.chunkify.hashfile import hash_file
from wsvcs.server import Server
from wsvcs.src.packages import *
from wsvcs.src.manifest import *
from websockets.sync.client import connect, ClientConnection
from pathlib import Path
from wsvcs.src.datastructures import *


from pickle import loads, dumps
import asyncio
import wsvcs
import tqdm
import sys
import re


class CLI:
    def __init__(self):
        self.project_root = Path().absolute()

    def init(self):
        # Check wsvcs path
        if self.wsvcs_path.exists():
            sys.stderr.write("error: WSVCS path exists\n")
            return

        # Create wsvcs environment
        self.wsvcs_path.mkdir()
        self.ignore_file.touch()
        self.manifest_file.touch()

        # Save default manifest
        get_default_manifest(self.project_root).save(self.manifest_file)

        # Complete
        print("Ready!")

    @staticmethod
    def deploy():
        server = Server()
        asyncio.run(server.run())

    def get_dotignore(self):
        return DotIgnore().initialize(
            [self.project_root / x for x in self.get_manifest()['project']['ignore']]
        ).optimize()

    def push(self):
        mfest = self.get_manifest()

        with connect(f"ws://{mfest['sync']['server']}") as websocket:
            print("Sending pub request")
            websocket.send('pub')

            print("Sending room name")
            websocket.send(dumps(room_package(self.project_root.name)))

            print("Enter to console")
            while True:
                command = input(": ")
                if re.fullmatch('subs', command):
                    websocket.send(dumps(refresh_package()))
                    print(f'Subscribers: {loads(websocket.recv())['subs']}')

                elif re.fullmatch('sync', command):
                    websocket.send(dumps(sync_package()))
                    break

                else:
                    print('Invalid command')

            print("Hashing packages")
            hashes_packages = dumps(
                {
                    str(path): hash_file(self.project_root / path)
                    for path in tqdm.tqdm(
                        walktree(
                            self.project_root,
                            self.get_dotignore()
                        )
                    )
                }
            )

            print("Sending path2hash package")
            self.send_chunked_package(
                websocket,
                split_package_to_chunks(hashes_packages)
            )

            print("Receiving missed files request")
            requested_packages = self.receive_chunked_package(websocket)['packages']

            print("Sending files as chunks")
            for filepath in tqdm.tqdm(requested_packages):
                with open(self.project_root / filepath, 'rb') as f:
                    self.send_chunked_package(
                        websocket,
                        read_in_chunks(
                            f,
                            path = filepath
                        )
                    )

    def pull(self):
        mfest = self.get_manifest()
        with connect(f"ws://{mfest['sync']['server']}") as websocket:
            print('Sending pull request')
            websocket.send('sub')

            print('Sending project name')
            websocket.send(
                dumps(
                    connect_package(mfest['project']['name'])
                )
            )

            print("Waiting for path and hash surjection")
            path_and_hash = Surjection().add_dict_as_key2val(
                self.receive_chunked_package(websocket)
            )

            print("Grouping files")
            files_to_update, files_to_delete, files_to_move, new_files = self.group_files(path_and_hash)

            print("Deleting files")
            self.delete_files(files_to_delete)

            print("Moving files")
            self.move_files(files_to_move)

            print("Sending missed files request")
            self.send_chunked_package(
                websocket,
                split_package_to_chunks(
                    dumps(missed_package(list(new_files | files_to_update))),
                )
            )

            print("Receive missed files chunks")

            for package in self.receive_chunked_package_as_chunks(websocket):
                full_path = self.project_root / package['path']
                full_path.parent.mkdir(parents=True, exist_ok=True)
                full_path.touch(exist_ok=True)
                with open(full_path, 'ab+') as f:
                    f.write(package['data'])

    def cli(self):
        while True:
            command = input("[client]: ").strip()
            if command in ('exit', 'q'):
                return 0

            elif command == 'run':
                print("You are already in client. The statement does not have any affect.")

            elif command in wsvcs.valid_commands:
                self.__getattribute__(command)()

            else:
                print("Invalid command.")

    @property
    def wsvcs_path(self):
        return self.project_root / 'wsvcs'

    @property
    def ignore_file(self):
        return self.wsvcs_path / '.wsvcsignore'

    @property
    def manifest_file(self):
        return self.wsvcs_path / 'manifest.toml'

    @staticmethod
    def send_chunked_package(websocket: ClientConnection, chunk_generator):
        for chunk, path in chunk_generator:
            websocket.send(
                dumps(
                    data_chunk_package(chunk, path)
                )
            )
        websocket.send(dumps(complete()))

    @staticmethod
    def receive_chunked_package_as_chunks(websocket: ClientConnection):
        while True:
            package = loads(websocket.recv())
            if package['type'] == 'complete':
                break
            elif package['type'] == 'chunk':
                yield package

    @staticmethod
    def receive_chunked_package(websocket: ClientConnection):
        full_package = b''
        while True:
            package = loads(websocket.recv())
            if package['type'] == 'complete':
                break
            elif package['type'] == 'chunk':
                full_package += package['data']
        return loads(full_package)

    def group_files(self, path_hash_sur: Surjection) -> tuple[set, set, set, set]:
        files_to_update = set()
        files_to_delete = set()
        files_to_move   = set()
        files_to_save   = set()

        for short_path in walktree(self.project_root, dot_ignore=self.get_dotignore()):
            short_path = str(short_path)
            long_path = self.project_root / short_path
            file_hash = hash_file(long_path)
            # case 1: files at the same directory
            if short_path in path_hash_sur:
                if path_hash_sur[short_path] == file_hash:
                    # same file
                    files_to_save.add(short_path)
                else:
                    # update
                    print(f"[U] {short_path}")
                    files_to_update.add(short_path)

            # case 2: same files at the difference folders
            elif file_hash in path_hash_sur:
                # move                 <from>         <to>
                files_to_move.add((short_path, path_hash_sur[file_hash]))
                print(f"[M] {short_path} -> {path_hash_sur[file_hash]}")

            # case 3: waste file
            else:
                # waste
                files_to_delete.add(short_path)
                print(f"[D] {short_path}")

        # case 4: new files
        new_files = set(path_hash_sur.from_keys()).difference(files_to_save)

        return files_to_update, files_to_delete, files_to_move, new_files

    def delete_files(self, files_to_delete: set[Path]):
        for file in files_to_delete:
            full_path = self.project_root / file
            print(f'...[ Removing file {full_path} ]...')

    def move_files(self, files_to_move: set[Path]):
        for file in files_to_move:
            full_path = self.project_root / file
            print(f'...[ Moving file {full_path} ]...')

    def get_manifest(self):
        mfest = Manifest()
        mfest.read_manifest(self.manifest_file)
        return mfest


__all__ = [
    'CLI'
]
