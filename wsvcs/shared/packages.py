def status_ok():
    return {
        'type': 'ok',
    }


def complete():
    return {
        'type': 'complete',
    }


def refresh_package():
    return {
        'type': 'refresh'
    }


def subscribers_package(subs: list):
    return {
        'type': 'subscribers',
        'subs': subs
    }


def role_package(role: str):
    return {
        'type': 'role',
        'role': role
    }


def room_package(room_name: str):
    return {
        'type': 'room',
        'room': room_name
    }


def rooms_package(rooms: list):
    return {
        'type': 'rooms',
        'rooms': rooms
    }


def sync_package():
    return {
        'type': 'sync'
    }


def connect_package(room: str):
    return {
        'type': 'connect',
        'room': room
    }


def data_chunk_package(data):
    return {
        'type': 'chunk',
        'data': data,
    }


def missed_package(packages: list):
    return {
        'type': 'to_download',
        'packages': packages
    }
