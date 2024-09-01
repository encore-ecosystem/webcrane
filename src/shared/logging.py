from datetime import datetime


def lazy_factory(type_: str):
    return lambda msg: print(f"[{datetime.now().strftime('%H:%M:%S')}] [{type_}]: {msg}")


info = lazy_factory('INFO')
crit = lazy_factory('CRIT')

__all__ = [
    'info',
    'crit'
]
