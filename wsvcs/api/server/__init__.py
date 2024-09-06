from websockets import WebSocketServerProtocol
from configparser import ConfigParser
from wsvcs.shared.logging import *
from websockets.server import serve
from wsvcs.shared.packages import *

import asyncio
import pickle
import json


class Server:
    def __init__(self):
        self.rooms = {}

    async def run(self, config: ConfigParser):
        info('Start As Server')
        ip   = config['Host']['ip']
        port = int(config['Host']['port'])
        async with serve(self.bootstrap, ip, port):
            print('Bootstrap has started')
            await asyncio.get_running_loop().create_future()

    async def bootstrap(self, websocket: WebSocketServerProtocol):
        role = json.loads(await websocket.recv())['role']

        match role:
            case 'sub':
                # Update process
                while True:
                    package = json.loads(await websocket.recv())
                    if package['type'] == 'refresh':
                        await websocket.send(json.dumps(rooms_package(list(self.rooms.keys()))))
                    elif package['type'] == 'connect':
                        self.rooms[package['room']]['subscribers'].append(websocket)
                        break
                    else:
                        print(f'Unexpected package: {package}')

                # Sync process
                files = set(json.loads(await websocket.recv())['packages'])
                self.rooms[package['room']]['status'] += 1
                self.rooms[package['room']]['files'] = self.rooms[package['room']]['files'].union(files)

                while self.rooms.get(package['room'], None) is not None:
                    await asyncio.sleep(1)

            case 'pub':
                room_name = json.loads(await websocket.recv())['room']
                self.rooms[room_name] = {'subscribers': [], 'available': True, 'status': 0, 'files': set()}
                # Update process
                while True:
                    package = json.loads(await websocket.recv())
                    if package['type'] == 'refresh':
                        await websocket.send(json.dumps(subscribers_package(
                            [f"{ws.remote_address[0]}:{ws.remote_address[1]}" for ws in self.rooms[room_name]['subscribers']]
                        )))
                    elif package['type'] == 'sync':
                        break
                    else:
                        print(f'Unexpected package: {package}')

                # Sync process
                self.rooms[room_name]['available'] = False
                hashes = await websocket.recv()

                # - send hashes
                for sub in self.rooms[room_name]['subscribers']:
                    await sub.send(hashes)

                while self.rooms[room_name]['status'] != len(self.rooms[room_name]['subscribers']):
                    await asyncio.sleep(0.2)

                m = missed_package(list(self.rooms[room_name]['files']))
                await websocket.send(json.dumps(m))
                while True:
                    package = pickle.loads(await websocket.recv())
                    if package['type'] == 'complete':
                        break
                    elif package['type'] == 'chunk':
                        for sub in self.rooms[room_name]['subscribers']:
                            await sub.send(pickle.dumps(package))

                del self.rooms[room_name]


__all__ = [
    'Server'
]
