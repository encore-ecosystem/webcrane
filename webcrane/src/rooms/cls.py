import websockets


class Rooms:
    def __init__(self):
        self.rooms = {}

        self.locked   = set()
        self.statuses = {}

    def get_num_of_subs(self, room_name: str) -> int:
        return len(self.rooms.get(room_name, []))

    def create_room(self, room_name: str):
        if room_name not in self.rooms:
            self.rooms[room_name] = []
            self.statuses[room_name] = 0

    def lock(self, room_name: str):
        self.locked.add(room_name)

    def unlock(self, room_name: str):
        self.locked.discard(room_name)

    def get_subs(self, room_name: str) -> list:
        return [data for data in self.rooms.get(room_name, [])]

    def get_websockets(self, room_name: str) -> list:
        return [data['websocket'] for data in self.rooms.get(room_name, [])]

    def get_addresses(self, room_name: str) -> list:
        return [data['address'] for data in self.rooms.get(room_name, [])]

    def get_missing_files(self, room_name: str) -> list:
        return [data['missing_files'] for data in self.rooms.get(room_name, [])]

    def get_missing_files_from(self, room_name: str, sub_address: str) -> list:
        sub_index = 0
        while sub_index < len(self.rooms.get(room_name, [])):
            if self.rooms[room_name][sub_index]['address'] == sub_address:
                return self.rooms[room_name][sub_index]['missing_files']
            sub_index += 1

    def add_sub(self, room_name: str, sub_address: str, sub_websocket: websockets.WebSocketServerProtocol) -> bool:
        self.create_room(room_name)
        if room_name not in self.locked:
            self.rooms[room_name].append(
                {'address': sub_address, 'websocket': sub_websocket, 'missing_files': set()}
            )
            return True
        return False

    def add_missed_files(self, room_name: str, sub_address: str, missed_files: set):
        sub_index = 0
        while sub_index < len(self.rooms.get(room_name, [])):
            if self.rooms[room_name][sub_index]['address'] == sub_address:
                self.rooms[room_name][sub_index]['missing_files'] |= missed_files
            sub_index += 1

    def remove_sub(self, room_name: str, sub_address: str):
        # Remove sub
        sub_index = 0
        while sub_index < len(self.rooms.get(room_name, [])):
            if self.rooms[room_name][sub_index]['address'] == sub_address:
                popped = self.rooms[room_name].pop()
                if sub_index + 1 != len(self.rooms[room_name]):
                    self.rooms[room_name][sub_index] = popped
                break
            sub_index += 1

        # Clear room if there are no subs in room
        self.remove_room(room_name)

    def remove_room(self, room_name: str):
        if room_name in self.rooms:
            self.unlock(room_name)
            del self.rooms[room_name], self.statuses[room_name]

    def increment_status(self, room_name: str):
        self.statuses[room_name] += 1

    def get_status(self, room_name: str):
        return self.statuses.get(room_name, 0)


__all__ = ['Rooms']
