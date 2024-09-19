import websockets

from webcrane.src.chunkify.chunk_reader import *
from webcrane.src.filepath.walktree import *
from webcrane.src.chunkify.hashfile import *
from webcrane.server import Server
from webcrane.src.packages import *
from webcrane.src.manifest import *
from websockets.sync.client import connect, ClientConnection
from pathlib import Path
from webcrane.src.datastructures import *
from webcrane import PACKAGE_MAX_SIZE
from pickle import loads, dumps
from termcolor import colored
from webcrane.src.merge import merge_files
from webcrane.src.tui import input_with_default
import concurrent.futures
import asyncio
import shutil
import webcrane
import tqdm
import sys
import re
import os


class CLI:
    def __init__(self):
        self.project_root = Path().absolute()

    def init(self):
        # Check webcrane path
        if self.webcrane_path.exists():
            sys.stderr.write("error: webcrane path exists\n")
            return

        # Create webcrane environment
        self.webcrane_path.mkdir()
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
        print(f"Server is {mfest['sync']['server']}")
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

            print(f"Hashing packages ({webcrane.HASHING_THREADS}) threads")
            hashes_packages = {}
            file_paths = list(walktree(self.project_root, self.get_dotignore()))
            with concurrent.futures.ThreadPoolExecutor(max_workers=webcrane.HASHING_THREADS) as executor:
                future_to_path = {executor.submit(process_file, self.project_root, path): path for path in file_paths}
                for future in tqdm.tqdm(concurrent.futures.as_completed(future_to_path), total=len(file_paths)):
                    path, file_hash = future.result()
                    hashes_packages[path] = file_hash
            hashes_packages = dumps(hashes_packages)

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

            pbar = tqdm.tqdm(requested_packages)
            for filepath in pbar:
                # progress bar description
                if len(filepath) <= webcrane.LENGTH_OF_PATH_IN_PBAR:
                    desc = filepath
                else:
                    desc = '...'+filepath[-webcrane.LENGTH_OF_PATH_IN_PBAR + 3:]

                pbar.set_description_str(
                    desc="Working on: " + colored(f"{desc:>{webcrane.LENGTH_OF_PATH_IN_PBAR}}", "cyan")
                )

                # logic
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
        print(f"Server is {mfest['sync']['server']}")
        with connect(f"ws://{mfest['sync']['server']}") as websocket:
            print('Sending pull request')
            websocket.send('sub')

            merge = input_with_default("Enter to merge mode?", default='No').lower().strip() == 'yes'

            print('Sending project name')
            websocket.send(
                dumps(
                    connect_package(mfest['project']['name'])
                )
            )
            try:
                print("Waiting for path and hash surjection")
                path_and_hash = Surjection().add_dict_as_key2val(
                    self.receive_chunked_package(websocket)
                )

                print("Grouping files")
                files_to_update, files_to_delete, files_to_move, new_files = self.group_files(path_and_hash)

                print("Deleting files")
                self.delete_files(files_to_delete)
                (not merge) and self.delete_files(files_to_update)

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
                current_merge_file = ''
                current_merge_file_path = None

                for package in self.receive_chunked_package_as_chunks(websocket):
                    if package['type'] == 'full':
                        extracted_packages = package['data']
                    else:
                        extracted_packages = [package]
                    for pck in extracted_packages:
                        # Create context
                        full_path = self.project_root / pck['path']
                        full_path.parent.mkdir(parents=True, exist_ok=True)
                        full_path.touch(exist_ok=True)

                        # Merge files
                        if pck in files_to_update:
                            # new file
                            if pck['path'] != current_merge_file_path:
                                # merge file
                                if current_merge_file_path is not None:
                                    print(f"Merging {current_merge_file_path}")
                                    with open(current_merge_file_path, 'r') as f:
                                        merged = merge_files(f.read(), current_merge_file)
                                    with open(current_merge_file_path, 'w') as f:
                                        f.write(merged)

                                # update current merge
                                current_merge_file = ''
                                current_merge_file_path = pck['path']

                            current_merge_file += pck['data']

                        # Update files
                        else:
                            with open(full_path, 'ab+') as f:
                                f.write(pck['data'])
                        print(f"Accepted data for: {colored(pck['path'], "cyan")}")

            except websockets.ConnectionClosedOK:
                print("Connection closed. Project don't synchronize")

    def cli(self):
        while True:
            command = input("[client]: ").strip()
            if command in ('exit', 'q'):
                return 0

            elif command == 'run':
                print("You are already in client. The statement does not have any affect.")

            elif command in webcrane.valid_commands:
                self.__getattribute__(command)()

            else:
                print("Invalid command.")

    @property
    def webcrane_path(self):
        return self.project_root / 'webcrane'

    @property
    def ignore_file(self):
        return self.webcrane_path / '.webcraneignore'

    @property
    def manifest_file(self):
        return self.webcrane_path / 'manifest.toml'

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
                    print(f"{colored("[U]", "magenta")}: {short_path}")
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
        while len(files_to_delete) > 0:
            file = files_to_delete.pop()
            full_path = self.project_root / file
            if full_path.exists() and full_path.is_file():
                print(f"{colored("[D]", "light_red")}: {full_path}")
                os.remove(full_path)

            parent = full_path.parent
            while parent != self.project_root and len(os.listdir(parent)) == 0:
                print(f"{colored("[D]", "light_red")}: deleting empty folder: {parent}")
                shutil.rmtree(parent)
                parent = parent.parent

    def move_files(self, files_to_move: set[tuple[Path, Path]]):
        while len(files_to_move) > 0:
            src, dst = files_to_move.pop()
            print(f"{colored("[M]", "yellow")}: {src} -> {dst}")

            src = self.project_root / src
            dst = self.project_root / dst

            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(src, dst)

            parent = src.parent
            while parent != self.project_root and len(os.listdir(parent)) == 0:
                print(f"{colored("[M]", "yellow")}: deleting empty folder: {parent}")
                shutil.rmtree(parent)
                parent = parent.parent

    def get_manifest(self):
        mfest = Manifest()
        mfest.read_manifest(self.manifest_file)
        return mfest


__all__ = [
    'CLI'
]
