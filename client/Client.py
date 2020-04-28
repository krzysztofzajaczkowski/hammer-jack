import yaml
import socket
import time


class Client(object):
    def __init__(self, username):
        with open("appsettings.yaml", "r") as config_file:
            config = yaml.safe_load(config_file)
            server_credentials = config['ServerCredentials']
            self.server_address = server_credentials['Address']
            self.server_port = server_credentials['Port']
        self.username = username
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self):
        try:
            self.socket.connect((self.server_address, self.server_port))
            return 0
        except socket.error as msg:
            print(f"Couldn't connect: {msg}")
            self.socket.close()
            return -1

    def join_queue(self):
        message = f"{self.username}♞JOIN_QUEUE"
        self.socket.send(message.encode())
        data = self.socket.recv(2048)
        data = data.decode()
        print(f"Response from server: {data}")
        if data == f"{self.username}♞JOINED_QUEUE":
            print("Joined queue...")
            print("Press CTRL + C to leave")
            self.wait_in_queue()
        if data == f"{self.username}♞REJECTED_QUEUE":
            print("Couldn't join queue...") # REJECTED_QUEUE -> Server cannot establish user(sth like keyError if user
            # with the same username already exists)
            self.socket.shutdown(socket.SHUT_RDWR)
            self.socket.close()

    def wait_in_queue(self):
        try:
            while True:
                message = f"{self.username}♞IN_QUEUE"
                self.socket.send(message.encode())
                data = self.socket.recv(2048)
                data = data.decode()
                print(f"Response from server: {data}")
                if data == "DISCONNECT":
                    print("Server closed connection")
                    self.socket.shutdown(socket.SHUT_RDWR)
                    self.socket.close()
                    break
                time.sleep(1.0)
        except KeyboardInterrupt:
            print("\nLeaving queue")
            message = f"{self.username}♞LEAVE_QUEUE"
            self.socket.send(message.encode())
            self.socket.shutdown(socket.SHUT_RDWR)
            self.socket.close()