from webcrane.actors.client import Client
from termcolor import cprint
import webcrane


class CLI(Client):
    def cli(self):
        while True:
            command = input("[client]: ").strip()
            if command in ('exit', 'q'):
                return 0

            elif command == 'run':
                cprint("You are already in client. The statement does not have any affect.", 'red')

            elif command in webcrane.valid_commands:
                self.__getattribute__(command)()

            else:
                cprint("Invalid command.", 'red')


__all__ = ['CLI']
