from wsvcs.src.chunkify.chunk_reader import *
from wsvcs.src.filepath.walktree import walktree
from wsvcs.src.chunkify.hashfile import hash_file
from wsvcs.server import Server
from wsvcs.src.packages import *
from wsvcs.src.manifest import *
from websockets.sync.client import connect, ClientConnection
from pathlib import Path
from wsvcs.src.datastructures import *
from wsvcs import PACKAGE_MAX_SIZE

from pickle import loads, dumps
import asyncio
import shutil
import wsvcs
import tqdm
import sys
import re
import os


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
            cache = []
            cache_size = 0
            for filepath in tqdm.tqdm(requested_packages):
                file_size = (self.project_root / filepath).stat().st_size
                with open(self.project_root / filepath, 'rb') as f:
                    if file_size > PACKAGE_MAX_SIZE:
                        self.send_chunked_package(
                            websocket,
                            read_in_chunks(
                                f,
                                path=filepath
                            )
                        )
                    else:
                        # There is size in cache for this file
                        if PACKAGE_MAX_SIZE - cache_size >= file_size:
                            cache.append(data_chunk_package(f.read(), path=filepath))
                            cache_size += file_size

                        # There is no size in cache for this file
                        else:
                            # Send cumulative cache
                            if cache:
                                websocket.send(dumps(full_data_package(cache)))

                            # update cache
                            cache = [data_chunk_package(f.read(), path=filepath)]
                            cache_size = file_size
            if cache:
                websocket.send(dumps(full_data_package(cache)))

            print("Sending close request")
            websocket.send(dumps(close_package()))

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
            self.delete_files(files_to_update)

            print("Moving files")
            self.move_files(files_to_move)

            print("Sending missed files request")
            self.send_chunked_package(
                websocket,
                split_package_to_chunks(
                    dumps(missed_package(list(new_files | files_to_update))),
                )
            )

            print("Receive chunks with missed files")
            for package in self.receive_chunked_package_as_chunks(websocket):
                if package['type'] == 'full':
                    extracted_packages = package['data']
                else:
                    extracted_packages = [package]
                for pck in extracted_packages:
                    full_path = self.project_root / pck['path']
                    full_path.parent.mkdir(parents=True, exist_ok=True)
                    full_path.touch(exist_ok=True)
                    with open(full_path, 'ab+') as f:
                        f.write(pck['data'])

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
            elif package['type'] in ('chunk', 'full'):
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

            # case 3: waste file
            else:
                # waste
                files_to_delete.add(short_path)

        # case 4: new files
        new_files = set(path_hash_sur.from_keys()).difference(files_to_save)

        return files_to_update, files_to_delete, files_to_move, new_files

    def delete_files(self, files_to_delete: set[Path]):
        for file in files_to_delete:
            full_path = self.project_root / file
            if full_path.exists() and full_path.is_file():
                print(f"[D] {full_path}")
                os.remove(full_path)

            parent = full_path.parent
            while parent != self.project_root and len(os.listdir(parent)) == 0:
                print(f"[D] deleting empty folder: {parent}")
                shutil.rmtree(parent)
                parent = parent.parent

    def move_files(self, files_to_move: set[tuple[Path, Path]]):
        while len(files_to_move) > 0:
            src, dst = files_to_move.pop()
            print(f"[M] {src} -> {dst}")

            src = self.project_root / src
            dst = self.project_root / dst

            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(src, dst)

            parent = src.parent
            while parent != self.project_root and len(os.listdir(parent)) == 0:
                print(f"[M] deleting empty folder: {parent}")
                shutil.rmtree(parent)
                parent = parent.parent

    def get_manifest(self):
        mfest = Manifest()
        mfest.read_manifest(self.manifest_file)
        return mfest


__all__ = [
    'CLI'
]
