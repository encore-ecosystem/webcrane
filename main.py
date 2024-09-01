from src.server import Server
from src.client import Client
from src.shared.modes import Mode
from src import wsvcs_mode

import asyncio


async def main():
    service = None

    match wsvcs_mode:
        case Mode.SERVER:
            service = Server()
        case Mode.CLIENT:
            service = Client()

    await service.run()


if __name__ == '__main__':
    asyncio.run(main())
