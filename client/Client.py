import yaml
import socket
import time
import ast

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
        message = f"{self.username}♞GAME_STATE"
        self.socket.send(message.encode())
        data = self.socket.recv(2048)
        data = data.decode()
        try:
            data = int(data)
            # if data is int, then it's a place in queue
            # print(f"Your place in queue: {data}")
            print("Press CTRL + C to leave")
            self.wait_in_queue()
        except ValueError:
            # if data is not int, then we're not in queue
            print("Couldn't join queue...")
            self.socket.shutdown(socket.SHUT_RDWR)
            self.socket.close()

    def wait_in_queue(self):
        try:
            while True:
                # message = f"{self.username}♞GAME_STATE"
                message = f"GAME_STATE"
                self.socket.send(message.encode())
                data = self.socket.recv(2048)
                data = data.decode()
                try:
                    # if data is int, then it's a place in queue
                    data = int(data)
                    print(f"Your place in queue: {data}")
                except ValueError:
                    try:
                        # if data is not int, then it's a list of users to create game
                        data = ast.literal_eval(data)
                        print(f"Response from server: {data}")
                        # prepare to connect with others
                        break
                    except ValueError:
                        # if not list, then server closed connection
                        print("Server closed connection")
                        self.socket.close()
                        break
                time.sleep(1.0)
        except KeyboardInterrupt:
            print("\nLeaving queue")
            message = f"{self.username}♞LEAVE_QUEUE"
            self.socket.send(message.encode())
            self.socket.shutdown(socket.SHUT_RDWR)
            self.socket.close()
        self.socket.shutdown(socket.SHUT_RDWR)
        self.socket.close()
