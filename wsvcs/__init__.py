#
# Parse arguments
#
from argparse import ArgumentParser

# parser = ArgumentParser(
#     prog='wsvcs',
# )
# parser.add_argument('-m', '--mode')
# args = parser.parse_args()

# Resolve mode
from wsvcs.shared.modes import Mode
mode = 'server'
match mode:
    case 'server':
        MODE = Mode.SERVER
    case 'client':
        MODE = Mode.CLIENT
    case _:
        raise ValueError(f'Unknown mode {mode}')

#
# Read Config File
#
from configparser import ConfigParser
from pathlib import Path

CONFIG_PATH = Path() / 'config.ini'

config = ConfigParser()
if CONFIG_PATH.exists():
    config.read(CONFIG_PATH)
else:
    CONFIG_PATH.touch()


#
def get_option(section: str, option: str):
    if not config.has_section(section):
        raise ValueError(f"Config should have {section} section")

    if not config.has_option(section, option):
        raise ValueError(f"Option {option} not found in config")

    return config[section][option]


# get host
HOST = get_option('Host', 'ip')
PORT = get_option('Host', 'port')

# get options
MAX_BYTES_IN_CHUNK = get_option('Options', 'max_bytes_in_chunk')
LAST_HOST = config['Options']['last_host'] if config.has_option('Options', 'last_host') else None
LAST_PROJECT_PATH = config['Options']['last_project_path'] if config.has_option('Options', 'last_project_path') else None

__all__ = [
    HOST, PORT, MODE, MAX_BYTES_IN_CHUNK
]
