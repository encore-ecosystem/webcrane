from wsvcs.shared.config import parse_config_from_file
from wsvcs.cli import CLI

import wsvcs


def start(mode: str):
    # Read the config
    config = parse_config_from_file(wsvcs.CONFIG_PATH)

    # Create CLI
    cli = CLI(config)

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
