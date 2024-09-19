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


class Client:
    def __init__(self):
        self.project_root = Path().absolute()

    def init(self):
        # Check webcrane path
        if self.webcrane_path.exists():
            print(colored("error: webcrane path exists", color='red'))
            return

        # Create webcrane environment
        self.webcrane_path.mkdir()
        self.ignore_file.touch()
        self.manifest_file.touch()

        # Save default manifest
        get_default_manifest(self.project_root).save(self.manifest_file)

        # Complete
        print("Ready!")

    def get_dotignore(self):
        return DotIgnore().initialize(
            [self.project_root / x for x in self.get_manifest()['project']['ignore']]
        ).optimize()

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

    def get_manifest(self):
        mfest = Manifest()
        mfest.read_manifest(self.manifest_file)
        return mfest


__all__ = ['Client']
