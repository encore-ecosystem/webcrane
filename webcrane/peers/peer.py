from webcrane.src.packages import *
from webcrane.src.default import get_default_manifest
from webcrane.src.manifest import Manifest
from webcrane.src.datastructures import Surjection, DotIgnore
from termcolor import cprint, colored
from typing import AsyncIterator, Iterator
from pathlib import Path
from webcrane.src.filepath import walktree, threaded_grouping, threaded_hashing
from websockets.sync.client import connect, ClientConnection
from websockets import WebSocketServerProtocol
from webcrane.src.tui import pretty_pbar
from webcrane import HASHING_THREADS, GROUPING_THREADS

import shutil
import pickle
import tqdm
import re
import os


class Peer:
    def __init__(self):
        self.project_root = Path().absolute()

    # ===========================
    # WebCrane Builtin Behaviour
    # ===========================
    async def init(self):
        # Check webcrane path
        if self.webcrane_path.exists():
            cprint("error: webcrane path exists", color='red')
            return

        # Create webcrane environment
        self.webcrane_path.mkdir()
        self.ignore_file.touch()
        self.manifest_file.touch()

        # Save default manifest
        get_default_manifest(self.project_root).save(self.manifest_file)

        # Complete
        cprint("Complete!", color='green')

    async def push(self):
        mfest = self.get_manifest()
        print(f"Server is {mfest['sync']['server']}")
        with connect(f"ws://{mfest['sync']['server']}") as websocket:
            print("Sending role package")
            await self.send(websocket, package_chunk_generator(RolePackage('push')))

            print("Sending project name")
            await self.send(websocket, package_chunk_generator(ProjectPackage(project_name=mfest['project']['name'])))

            print("Entering to console")
            while True:
                command = input(": ")
                if re.fullmatch('subs', command):
                    await self.send(websocket, package_chunk_generator(RefreshPackage([])))
                    refresh_package = await self.recv(websocket)
                    print(f'Subscribers: {refresh_package.data.get('subs', ['error'])}')

                elif re.fullmatch('sync', command):
                    await self.send(websocket, package_chunk_generator(CompletePackage()))
                    break

                else:
                    cprint('Invalid command', color='red')

            print("Sending hash of files")
            file_paths = list(walktree(self.project_root, self.get_dotignore()))
            await self.send_from_generator(websocket, threaded_hashing(
                self.project_root,
                file_paths,
                threads=HASHING_THREADS
            ))

            print("Receiving missing files request")
            missing_files_package = await self.recv(websocket)
            missing_files = missing_files_package.data.get('missing_files', [])

            print("Sending missed files")
            with tqdm.tqdm(missing_files) as pbar:
                for filepath in pbar:
                    await self.send_from_generator(websocket, file_generator(self.project_root, filepath, pbar))

            cprint("Complete!", 'green')
            await self.send(websocket, package_chunk_generator(ClosePackage()))

    async def pull(self):
        mfest = self.get_manifest()
        print(f"Server is {mfest['sync']['server']}")
        with connect(f"ws://{mfest['sync']['server']}") as websocket:
            print('Sending role package')
            await self.send(websocket, package_chunk_generator(RolePackage('pull')))

            print('Sending project name')
            await self.send(websocket, package_chunk_generator(ProjectPackage(project_name=mfest['project']['name'])))

            print("Waiting for hashes")
            hashes = Surjection()
            with tqdm.tqdm() as pbar:
                async for hash_package in self.recv_from_generator(websocket):
                    pbar.update(1)
                    pbar.set_description(pretty_pbar(0, hash_package.data['filepath']))
                    hashes.add_dict_as_key2val({hash_package.data['filepath'] : hash_package.data['hash']})
            pbar.close()

            print("Grouping files")
            files_to_update, files_to_delete, files_to_move, new_files = threaded_grouping(
                self.project_root,
                self.get_dotignore(),
                hashes,
                threads=GROUPING_THREADS
            )

            print("Deleting files")
            self.delete_files(files_to_delete)
            self.delete_files(files_to_update)

            print("Moving files")
            self.move_files(files_to_move)

            print("Sending missed files request")
            missed_files = new_files | files_to_update
            await self.send(websocket, package_chunk_generator(MissingFiles(missed_files)))

            print("Receive chunks with missed files")
            with tqdm.tqdm(missed_files) as pbar:
                last_path  = None
                last_chunk = 0
                for _ in pbar:
                    async for package in self.recv_from_generator(websocket):
                        assert isinstance(package, FileChunk)

                        full_path = self.project_root / package.data['local_path']
                        full_path.parent.mkdir(parents=True, exist_ok=True)
                        full_path.touch(exist_ok=True)
                        with open(full_path, 'ab+') as f:
                            f.write(package.data['data'])

                        last_chunk += 1
                        if full_path != last_path:
                            last_path = full_path
                            last_chunk = 0

                        pbar.set_description(pretty_pbar(last_chunk, package.data['local_path']))

            cprint("Complete!", 'green')

    # ===============
    # WebCrane Logic
    # ===============
    @staticmethod
    async def send(websocket: ClientConnection | WebSocketServerProtocol, chunk_generator):
        ssp = pickle.dumps(StartSection())
        websocket.send(ssp) if isinstance(websocket, ClientConnection) else (await websocket.send(ssp))

        for package in chunk_generator:
            package = pickle.dumps(package)
            websocket.send(package) if isinstance(websocket, ClientConnection) else (await websocket.send(package))

        esp = pickle.dumps(EndSection())
        websocket.send(esp) if isinstance(websocket, ClientConnection) else (await websocket.send(esp))

    async def send_from_generator(self, websocket: ClientConnection | WebSocketServerProtocol, generator: AsyncIterator[Package] | Iterator[Package]):
        await self.send(websocket, package_chunk_generator(StartGenerator()))

        if isinstance(generator, AsyncIterator):
            async for package in generator:
                await self.send(websocket, package_chunk_generator(package))
        else:
            for package in generator:
                await self.send(websocket, package_chunk_generator(package))

        await self.send(websocket, package_chunk_generator(EndGenerator()))

    @staticmethod
    async def recv(websocket: ClientConnection | WebSocketServerProtocol) -> Package:
        ssp = websocket.recv() if isinstance(websocket, ClientConnection) else (await websocket.recv())
        ssp = pickle.loads(ssp)
        assert isinstance(ssp, StartSection)

        pickled_package = b''
        while True:
            chunk = websocket.recv() if isinstance(websocket, ClientConnection) else (await websocket.recv())
            chunk = pickle.loads(chunk)
            if isinstance(chunk, EndSection):
                break
            pickled_package += chunk

        package = pickle.loads(pickled_package)
        return package.data['package']

    async def recv_from_generator(self, websocket: ClientConnection | WebSocketServerProtocol) -> AsyncIterator[Package]:
        sgp = await self.recv(websocket)
        assert isinstance(sgp, StartGenerator)
        while True:
            curr_package = await self.recv(websocket)
            if isinstance(curr_package, EndGenerator):
                break
            yield curr_package

    @property
    def webcrane_path(self):
        return self.project_root / 'webcrane'

    @property
    def ignore_file(self):
        return self.webcrane_path / '.webcraneignore'

    @property
    def manifest_file(self):
        return self.webcrane_path / 'manifest.toml'

    def get_manifest(self):
        mfest = Manifest()
        mfest.read_manifest(self.manifest_file)
        return mfest

    def get_dotignore(self):
        return DotIgnore().initialize(
            [self.project_root / x for x in self.get_manifest()['project']['ignore']]
        ).optimize()

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


__all__ = ['Peer']
