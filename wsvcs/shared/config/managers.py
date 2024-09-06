from configparser import ConfigParser
from pathlib import Path
from .validators import validate_chunks, validate_host


def validate_config(config: ConfigParser):
    validate_chunks(config)
    validate_host(config)


def get_default_config() -> dict:
    return {
        'Host': {
            'ip'   : '0.0.0.0',
            'port' : '8765',
        },
        'Chunks': {
            'max_bytes_per_chunk' : 1024,
        },
    }


def parse_config_from_file(config_file_path: Path) -> ConfigParser:
    config = ConfigParser()
    if config_file_path.exists():
        config.read(config_file_path)
    else:
        config_file_path.touch()
        default_config = get_default_config()
        for section in default_config.keys():
            config[section] = default_config[section]

        with open(config_file_path, 'w') as config_file:
            config.write(config_file)

    validate_config(config)
    return config


__all__ = ['parse_config_from_file']
