from abc import ABC, abstractmethod


class Socket(ABC):
    """
    This is the base class for all protocols
    """
    @abstractmethod
    def connect(self, host: str):
        pass

    @abstractmethod
    def disconnect(self):
        pass

    @abstractmethod
    def send(self, data: bytes):
        pass

    @abstractmethod
    def recv(self, num_bytes: int):
        pass

    @abstractmethod
    def __enter__(self):
        pass

    @abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


__all__ = [
    'Socket'
]
