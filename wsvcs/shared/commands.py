from enum import Enum


class Commands(Enum):
    APPROVE_CONNECTION = 'approve connection'
    ROOM_IS_READY = 'room is ready'
    SELECT_PUBLISHER_ROLE = 'select publisher role'
    SELECT_SUBSCRIBER_ROLE = 'select subscriber role'
    REFRESH_PUBLISHERS = 'refresh'


__all__ = [
    'Commands'
]
