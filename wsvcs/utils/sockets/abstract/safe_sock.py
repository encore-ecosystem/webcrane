from .socket import Socket
from abc import ABCMeta


class SafeSocket(Socket, metaclass=ABCMeta):
    """
    This is the class for all protocols that able to receipt check
    """
    pass


__all__ = [
    'SafeSocket'
]
