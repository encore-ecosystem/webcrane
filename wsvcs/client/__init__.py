import json

from websockets.sync.client import connect
from wsvcs.shared.abstract import Service
from wsvcs.shared.logging import *
from pathlib import Path
from wsvcs.client.walktree import walktree
from wsvcs.shared.packages import *
from wsvcs.shared.hashfile import hash_file
from wsvcs.shared.chunk_reader import read_in_chunks
from wsvcs.client.reverse_dict import reverse_dict

import pickle
import tqdm
import re


class Client(Service):
    def __init__(self, last_project_path, last_host):
        self.project_path = None
        self.last_project_path = last_project_path
        self.last_host = last_host

    async def run(self):
        info('Run client')

        # project path
        if self.last_project_path is not None and input(
                f"Use last project: {self.last_project_path}? [Y/n]: ").lower().strip() in ('', 'y'):
            self.project_path = Path(self.last_project_path)
        else:
            self.project_path = Path(input(f"Enter path to project root directory: "))
        assert self.project_path.exists(), 'Project path does not exist'

        # host
        if self.last_host is not None and input(f"Use last host: {self.last_host}? [Y/n]: ").lower().strip() in (
        '', 'y'):
            host = f"ws://{self.last_host}"
        else:
            host = f"ws://{input("Enter server address: ")}"

        # role
        role = input("Select role (pub/sub): ")
        assert role in ('pub', 'sub')

        # logic
        with connect(host) as websocket:
            websocket.send(json.dumps(role_package(role)))
            match role:
                case 'sub':
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
                    source_path_to_hash = json.loads(websocket.recv())
                    source_hash_to_path = reverse_dict(source_path_to_hash)
                    black_list = set()

                    files_to_update = set()  # todo
                    files_to_delete = set()  # todo
                    files_to_move   = set()  # todo
                    files_to_save   = set()  # todo

                    for filepath in walktree(Path(self.project_path), black_list):
                        filepath_short = Path(*filepath[0].parts[-filepath[1]:]).__str__()
                        file_hash = hash_file(filepath[0])[:8]
                        # case 1: files at the same directory
                        if filepath_short in source_path_to_hash:
                            if source_path_to_hash[filepath_short] != file_hash:
                                # update
                                files_to_update.add(filepath_short)
                            else:
                                # same file
                                files_to_save.add(filepath_short)

                        # case 2: same files at the difference folders
                        elif file_hash in source_hash_to_path:
                            # move
                            files_to_move.add((filepath_short, source_hash_to_path[file_hash]))

                        # case 3: waste file
                        else:
                            # waste
                            files_to_delete.add(filepath_short)

                    # case 4: new files
                    new_files = set(source_path_to_hash.keys()).difference(files_to_save)

                    # send
                    websocket.send(json.dumps(missed_package(list(new_files | files_to_update))))

                    while True:
                        package = pickle.loads(websocket.recv())
                        if package['type'] == 'complete':
                            break
                        elif package['type'] == 'chunk':
                            full_path = self.project_path / package['path']

                            full_path.parent.mkdir(parents=True, exist_ok=True)
                            full_path.touch(exist_ok=True)
                            with open(full_path, 'ab+') as f:
                                f.write(package['data'])

                case 'pub':
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
                    files_path = walktree(Path(self.project_path), black_list)
                    hashes = {Path(*filepath[0].parts[-filepath[1]:]).__str__(): hash_file(filepath[0])[:8] for filepath in files_path}
                    websocket.send(json.dumps(hashes))
                    packages = json.loads(websocket.recv())['packages']
                    for filepath in tqdm.tqdm(packages):
                        with open(self.project_path / filepath, 'rb') as f:
                            for chunk in read_in_chunks(f, chunk_size=16000):
                                websocket.send(pickle.dumps(file_chunk_package(filepath, chunk)))
                    websocket.send(pickle.dumps(complete()))


__all__ = [
    'Client'
]
