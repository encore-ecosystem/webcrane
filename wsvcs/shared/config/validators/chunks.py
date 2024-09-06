from configparser import ConfigParser


def validate_chunks(config: ConfigParser):
    assert config.has_section('Chunks')

    assert config.has_option('Chunks', 'max_bytes_per_chunk')


__all__ = ['validate_chunks']
