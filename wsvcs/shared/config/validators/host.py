from configparser import ConfigParser


def validate_host(config: ConfigParser):
    assert config.has_section('Host')

    assert config.has_option('Host', 'ip')
    assert config.has_option('Host', 'port')


__all__ = ['validate_host']
