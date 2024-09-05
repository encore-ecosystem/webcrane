from wsvcs.server import Server
from wsvcs.client import Client
from wsvcs.shared.modes import Mode
from wsvcs import MODE, LAST_HOST, LAST_PROJECT_PATH

import asyncio


async def cli():
    match MODE:
        case Mode.SERVER:
            await Server().run()
        case Mode.CLIENT:
            await Client(last_host=LAST_HOST, last_project_path=LAST_PROJECT_PATH).run()


def main():
    asyncio.run(cli())


if __name__ == '__main__':
    main()
