from wsvcs.shared.chunk_reader import *
from wsvcs.shared.tui import input_with_default
from wsvcs.api.walktree import walktree
from wsvcs.shared.hashfile import hash_file
from wsvcs.api.server import Server
from wsvcs.shared.packages import *

from websockets.sync.client import connect, ClientConnection
from configparser import ConfigParser
from typing import Optional
from pathlib import Path

from wsvcs.shared.surjection import Surjection

import asyncio
import tomllib
import tomli_w
import pickle
import wsvcs
import tqdm
import json
import sys
import re


class CLI:
    def __init__(self, config: ConfigParser):
        self.config = config
        self.project_root = Path().absolute()

    def init(self):
        # Check wsvcs path
        if self.wsvcs_path.exists():
            sys.stderr.write("error: WSVCS path exists\n")
            return

        # Create wsvcs folder
        self.wsvcs_path.mkdir()
        self.ignore_file.touch()
        self.manifest_file.touch()

        # Fill manifest
        manifest = self.get_manifest()

        manifest['project'] = {
            'authors': input_with_default('Enter authors separated by comma', 'unknown').split(','),
            'licence': input_with_default('Licence', 'MIT'),
            'server': input("Enter server host: ").strip(),
        }

        # Save manifest
        with open(self.manifest_file, "wb") as f:
            tomli_w.dump(manifest, f)

        print("Ready!")

    def deploy(self):
        server = Server()
        asyncio.run(server.run(self.config))

    def push(self):
        manifest = self.get_manifest()
        project_path = self.wsvcs_path.parent
        host = f"ws://{manifest['server']}"
        with connect(host) as websocket:
            websocket.send(json.dumps(role_package('pub')))
            websocket.send(json.dumps(room_package(input("Enter room name: "))))

            # Update process
            while True:
                command = input(": ")
                if re.fullmatch('subs', command):
                    websocket.send(json.dumps(refresh_package()))
                    print(f'Subscribers: {json.loads(websocket.recv())['subs']}')

                elif re.fullmatch('sync', command):
                    websocket.send(json.dumps(sync_package()))
                    break

                else:
                    print('Invalid command')

            # Sync process
            black_list = set()
            files_path = walktree(project_path, black_list)
            hashes = {self.convert_to_project_path(filepath): hash_file(filepath[0]) for filepath in files_path}

            websocket.send(json.dumps(hashes))

            # Read
            packages = json.loads(websocket.recv())['packages']
            for filepath in tqdm.tqdm(packages):
                with open(project_path / filepath, 'rb') as f:
                    self.send_chunked_package(websocket, read_in_chunks(f, chunk_size=1024))
            websocket.send(pickle.dumps(complete()))

    def pull(self):
        manifest = self.get_manifest()
        project_path = self.wsvcs_path.parent
        host = f"ws://{manifest['server']}"
        with connect(host) as websocket:
            websocket.send(json.dumps(role_package('sub')))
            # Update process
            while True:
                command = input("Enter command: ")
                if re.fullmatch('refresh', command):
                    websocket.send(json.dumps(refresh_package()))
                    print(f'Rooms: {json.loads(websocket.recv())['rooms']}')

                elif re.fullmatch('connect', command.split()[0]):
                    websocket.send(json.dumps(connect_package(command.split()[1])))
                    break

                else:
                    print('Invalid command')

            # Sync process
            print("Waiting for source files...")
            path_and_hash = Surjection()
            path_and_hash.add_dict_as_key2val(json.loads(websocket.recv()))
            black_list = self.get_blacklist()

            files_to_update = set()
            files_to_delete = set()  # todo
            files_to_move = set()  # todo
            files_to_save = set()

            for filepath in walktree(project_path, black_list):  # todo: move walktree and self.convert_to... to module
                filepath_short = self.convert_to_project_path(filepath)
                file_hash = hash_file(filepath[0])
                # case 1: files at the same directory
                if filepath_short in path_and_hash:
                    if path_and_hash[filepath_short] != file_hash:
                        # update
                        files_to_update.add(filepath_short)
                    else:
                        # same file
                        files_to_save.add(filepath_short)

                # case 2: same files at the difference folders
                elif file_hash in path_and_hash:
                    # move
                    files_to_move.add((filepath_short, path_and_hash[file_hash]))

                # case 3: waste file
                else:
                    # waste
                    files_to_delete.add(filepath_short)

            # case 4: new files
            new_files = set(path_and_hash.from_keys()).difference(files_to_save)

            # send missed packages request
            self.send_chunked_package(
                websocket,
                split_string_to_chunks(
                    string=json.dumps(missed_package(list(new_files | files_to_update))),
                    chunk_size=1024
                )
            )

            # receive missed packages
            for package in self.receive_chunked_package(websocket):
                full_path = project_path / package['path']
                full_path.parent.mkdir(parents=True, exist_ok=True)
                full_path.touch(exist_ok=True)
                with open(full_path, 'ab+') as f:
                    f.write(package['data'])

    def cli(self):
        while True:
            command = input("[cli]: ").strip()
            if command in ('exit', 'q'):
                return 0

            elif command == 'run':
                print("You are already in cli. The statement does not have any affect.")

            elif command in wsvcs.valid_commands:
                self.__getattribute__(command)()

            else:
                print("Invalid command.")

    def get_manifest(self) -> Optional[dict]:
        if self.manifest_file.exists():
            with open(self.manifest_file, "rb") as f:
                manifest = tomllib.load(f)
            return manifest
        return None

    @staticmethod
    def get_blacklist():
        return set()

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
    def convert_to_project_path(filepath: tuple[Path, int]):
        return Path(*filepath[0].parts[-filepath[1]:]).__str__()

    @staticmethod
    def send_chunked_package(websocket: ClientConnection, chunk_generator):
        for chunk in chunk_generator:
            websocket.send(
                pickle.dumps(
                    data_chunk_package(chunk)
                )
            )
        websocket.send(complete())

    @staticmethod
    def receive_chunked_package(websocket: ClientConnection):
        while True:
            package = pickle.loads(websocket.recv())
            if package['type'] == 'complete':
                break
            elif package['type'] == 'chunk':
                yield package


__all__ = [
    'CLI'
]
