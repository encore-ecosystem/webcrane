import websockets

from src.shared.abstract import Service
from src.shared.logging import *
from websockets.server import serve
import asyncio


class Server(Service):
    def __init__(self):
        self.clients = set()

    async def run(self):
        info('Start As Server')
        async with serve(self.bootstrap, "0.0.0.0", 8765):
            info('Bootstrap has started')
            await asyncio.get_running_loop().create_future()

    async def bootstrap(self, websocket: websockets.WebSocketServerProtocol):
        info(f"New client connected: {websocket.remote_address}")
        info("approving connection")
        await websocket.send("connection approved")
        info("Complete! Disconnecting....")


__all__ = [
    'Server'
]
