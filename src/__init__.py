#
# Parse arguments
#
from argparse import ArgumentParser

parser = ArgumentParser(
    prog='wsvcs',
)
parser.add_argument('-m', '--mode')
args = parser.parse_args()

# Resolve mode
from src.shared.modes import Mode
mode = args.mode.lower()
match mode:
    case 'server':
        wsvcs_mode = Mode.SERVER
    case 'client':
        wsvcs_mode = Mode.CLIENT
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
