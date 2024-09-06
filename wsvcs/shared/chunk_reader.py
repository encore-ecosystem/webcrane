def read_in_chunks(file_object, chunk_size: int = 1024):
    while True:
        data = file_object.read(chunk_size)
        if not data:
            break
        yield data


def split_string_to_chunks(string: str, chunk_size: int = 1024):
    n = len(string)
    shift = 0
    while shift < n:
        data = string[shift: shift+chunk_size]
        yield data
        shift += chunk_size


__all__ = [
    'read_in_chunks',
    'split_string_to_chunks'
]
