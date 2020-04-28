import socket


class Client(object):
    def __init__(self, username, server_address, server_port):
        self.server_address = server_address
        self.server_port = server_port
        self.username = username
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self):
        self.socket.connect((self.server_address, self.server_port))

    def join_queue(self):
        message = f"{self.username}♞JOIN_QUEUE"
        self.socket.send(message.encode())
        data = self.socket.recv(1024)
        data = data.decode()
        print(f"Came back from server: {data}")
        self.wait_in_queue()

    def wait_in_queue(self):
        while True:
            data = self.socket.recv(1024)
            data = data.decode()
            if data == "DISCONNECT":
                print("Server closed connection")
                break
            print(data)
