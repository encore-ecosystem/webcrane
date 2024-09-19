from webcrane import PACKAGE_MAX_SIZE


def read_in_chunks(file_object, path: str = ''):
    while True:
        data = file_object.read(PACKAGE_MAX_SIZE)
        if not data:
            break
        yield data, path


def split_package_to_chunks(pickled_package: bytes, path: str = ''):
    n = len(pickled_package)
    shift = 0
    while shift < n:
        data = pickled_package[shift: shift+PACKAGE_MAX_SIZE]
        yield data, path
        shift += PACKAGE_MAX_SIZE


__all__ = [
    'read_in_chunks',
    'split_package_to_chunks'
]
