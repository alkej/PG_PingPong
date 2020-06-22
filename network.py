import socket
import json


class Network:
    def __init__(self):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = ""

        self.port = 9091
        self.addr = (self.host, self.port)

        self.id = self.connect()

    def connect(self):
        self.client.connect(self.addr)
        return self.client.recv(10).decode()

    def send(self, data):
        # send data and get data
        try:
            json_data = json.dumps(data)
            self.client.send(bytes(json_data, encoding="utf-8"))
            raw_data = self.client.recv(2048)
            try:
                reply = json.loads(raw_data)
                return reply
            except json.decoder.JSONDecodeError:
                if raw_data == b'':
                    return None
        except socket.error as e:
            print(str(e))
            return None

    def close(self):
        self.client.close()
