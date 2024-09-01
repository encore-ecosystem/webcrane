from websockets.sync.client import connect
from src.shared.abstract import Service
from src.shared.logging import *


class Client(Service):
    async def run(self):
        info('Run client')
        with connect(f"ws://{input("Enter server address:")}") as websocket:
            websocket.send("Hello world!")
            message = websocket.recv()
            print(f"Received: {message}")


__all__ = [
    'Client'
]
