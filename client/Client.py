import yaml
import socket
import time
import ast
from PlayerConnectionThreadsBuilder import PlayerConnectionThreadsBuilder


class Client(object):
    def __init__(self, username):
        with open("appsettings.yaml", "r") as config_file:
            config = yaml.safe_load(config_file)
            server_credentials = config['ServerCredentials']
            self.server_address = server_credentials['Address']
            self.server_port = server_credentials['Port']
        self.username = username
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connections_threads = None

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
            # first response is a greeting
            print(data)
            # if data is int, then it's a place in queue
            # print(f"Your place in queue: {data}")
            print("Press CTRL + C to leave")
            self.wait_in_queue()
        except ValueError:
            # if data is not int, then we're not in queue
            print("Couldn't join queue...")
            self.socket.shutdown(socket.SHUT_RDWR)
            self.socket.close()

    def handle_threads(self):
        try:
            while True:
                end_threads = 1
                for connection_thread in self.connections_threads:
                    if connection_thread.status.is_connected == "connection_error":
                        connection_thread.status.to_kill = True
                    if connection_thread.status.is_connected == "connection_error":
                        end_threads = 0
                if end_threads:
                    for connection_thread in self.connections_threads:
                        connection_thread.status.to_kill = True
                    for connection_thread in self.connections_threads:
                        connection_thread.thread.join()
                    return
        except KeyboardInterrupt:
            for connection_thread in self.connections_threads:
                connection_thread.status.to_kill = True
            for connection_thread in self.connections_threads:
                connection_thread.thread.join()
            return

    def build_connections_threads(self, response_from_server):
        builder = PlayerConnectionThreadsBuilder()
        builder.convert_server_response_to_users_and_ports(response_from_server)
        builder.find_client_index_in_users(self.username)
        builder.prepare_connection_config_for_each_player()
        builder.get_number_of_active_connections()
        builder.prepare_client_connections_config()
        self.connections_threads = builder.build()

    def start_connection_threads(self):
        for connection_thread in self.connections_threads:
            connection_thread.start()

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
                        self.build_connections_threads(data)
                        self.start_connection_threads()
                        self.handle_threads()
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
