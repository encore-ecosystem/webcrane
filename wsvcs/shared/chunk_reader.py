def read_in_chunks(file_object, chunk_size: int = 256 * 1024, path: str = ''):
    while True:
        data = file_object.read(chunk_size)
        if not data:
            break
        yield data, path


def split_package_to_chunks(pickled_package: bytes, chunk_size: int = 256 * 1024, path: str = ''):
    n = len(pickled_package)
    shift = 0
    while shift < n:
        data = pickled_package[shift: shift+chunk_size]
        yield data, path
        shift += chunk_size


__all__ = [
    'read_in_chunks',
    'split_package_to_chunks'
]
