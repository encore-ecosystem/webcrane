from webcrane.client import CLI

import webcrane


def start(mode: str):
    # Create CLI
    cli = CLI()

    # Handle arguments
    if mode in webcrane.valid_commands:
        if mode == 'client':
            cli.cli()
        else:
            cli.__getattribute__(mode)()
    else:
        print('Unknown mode, please check manual with <webcrane --help>')


def main():
    start(webcrane.args.mode)


if __name__ == '__main__':
    main()
