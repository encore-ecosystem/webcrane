from src.server import Server
from src.client import Client
from src.shared.modes import Mode
from src import MODE, LAST_HOST, LAST_PROJECT_PATH

import asyncio


async def main():
    service = None

    match MODE:
        case Mode.SERVER:
            service = Server()
        case Mode.CLIENT:
            service = Client(last_host=LAST_HOST, last_project_path=LAST_PROJECT_PATH)

    await service.run()


if __name__ == '__main__':
    asyncio.run(main())
