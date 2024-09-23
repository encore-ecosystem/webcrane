from termcolor import cprint
from webcrane.peers.peer import Peer
from webcrane.peers.repeater import RepeaterPeer
import webcrane
import asyncio


async def cli(mode: str):
    match mode:
        case 'client':
            cprint("You are already in client. The statement does not have any affect.", 'red')
        case 'exit':
            exit(0)
        case 'deploy':
            await RepeaterPeer().run()
        case 'init':
            await Peer().init()
        case 'pull':
            await Peer().pull()
        case 'push':
            await Peer().push()
        case _:
            cprint("Unknown mode.", 'red')


async def async_main(mode: str):
    match mode:
        case 'cli':
            while True:
                await cli(input("[client]: ").strip())
        case _:
            await cli(mode)


def main():
    asyncio.run(async_main(webcrane.args.mode))


if __name__ == '__main__':
    main()
