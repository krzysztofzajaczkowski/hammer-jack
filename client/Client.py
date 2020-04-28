import socket


class Client(object):
    def __init__(self, username, server_address, server_port):
        self.server_address = server_address
        self.server_port = server_port
        self.username = username
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self):
        try:
            self.socket.connect((self.server_address, self.server_port))
            return 0
        except socket.error as msg:
            print(f"Couldn't connect: {msg}")
            return -1

    def join_queue(self):
        message = f"{self.username}♞JOIN_QUEUE"
        self.socket.send(message.encode())
        data = self.socket.recv(1024)
        data = data.decode()
        print(f"Came back from server: {data}")
        if data == f"{self.username}♞JOINED_QUEUE":
            print("Joined queue...")
            self.wait_in_queue()
        if data == f"{self.username}♞REJECTED_QUEUE":
            print("Couldn't join queue...")
            pass  # REJECTED_QUEUE -> Server cannot establish user(sth like keyError if user
            # with the same username already exists)

    def wait_in_queue(self):
        try:
            while True:
                # message = input("->")
                # message = self.username + '♞' + message
                # self.socket.send(message.encode())
                data = self.socket.recv(1024)
                data = data.decode()
                if data == "DISCONNECT":
                    print("Server closed connection")
                    break
                print(data)
        except KeyboardInterrupt:
            print("\nLeaving queue")
            message = f"{self.username}♞LEAVE_QUEUE"
            self.socket.send(message.encode())
