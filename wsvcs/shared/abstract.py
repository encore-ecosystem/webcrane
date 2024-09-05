from abc import ABC, abstractmethod


class Service(ABC):
    @abstractmethod
    async def run(self):
        pass


__all__ = [
    'Service'
]
