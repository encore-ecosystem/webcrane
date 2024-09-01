from enum import Enum


class Mode(str, Enum):
    SERVER = 'server'
    CLIENT = 'client'


__all__ = [
    'Mode'
]
