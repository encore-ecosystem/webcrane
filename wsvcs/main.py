from wsvcs.cli import CLI

import wsvcs


def start(mode: str):
    # Create CLI
    cli = CLI()

    # Handle arguments
    if mode in wsvcs.valid_commands:
        if mode == 'cli':
            cli.cli()
        else:
            cli.__getattribute__(mode)()
    else:
        print('Unknown mode, please check manual with <wsvcs --help>')


def main():
    start(wsvcs.args.mode)


if __name__ == '__main__':
    main()
