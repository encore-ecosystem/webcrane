from .abstract.safe_sock import SafeSocket


class WebSocket(SafeSocket):

    def __init__(self):
        self.host = None

    def connect(self, host: str):
        self.host = host

    def disconnect(self):
        self.host = None

    def send(self, data: bytes):
        pass

    def recv(self, num_bytes: int):
        pass

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
