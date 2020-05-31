import threading
import socket
import time
from Logger import Logger

class ConnectionThread(threading.Thread):
    def __init__(self, thread_status):
        threading.Thread.__init__(self)
        self.logger = Logger.get_logger('ConnectionThread')
        self.handler_status = thread_status
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.conn = None
        self.lock = threading.Lock()
        self.game_view = None
        self.main_game = None
        self.end_game = False
        self.established_connection = False
        self.numbers_of_errors = 0
        self.disconnected = False
        self.last_package = False
        self.max_numbers_of_errors = 5

    def set_game_view(self, game_view):
        self.game_view = game_view

    def set_main_game(self, main_game):
        self.main_game = main_game

    def run(self):
        try:
            while not self.handler_status.to_kill:
                if self.handler_status.is_connected != "connected":
                    if self.handler_status.is_active_connect:
                        self.connect()
                    else:
                        self.listen()
                else:
                    break
            if self.conn is not None:
               self.conn.settimeout(2.0)
            while not self.handler_status.to_kill:
                if self.end_game:
                    pass # send end_game message
                if not self.last_package:
                    self.send_counter()
                    self.get_counter()
                    if self.numbers_of_errors >= self.max_numbers_of_errors:
                        self.handler_status.to_kill = 1
                        self.handler_status.is_connected = 'connection_error'
                        self.disconnected = True
                    time.sleep(0.05)
        finally:
            self.logger.debug("Conn thread closed")
            self.kill()

    def set_message_to_send(self, message):
        while self.lock.locked():
            time.sleep(0.05)
        self.handler_status.msg_to_send = message

    def get_received_message(self):
        while self.lock.locked():
            time.sleep(0.05)
        msg = self.handler_status.received_msg
        return msg

    def is_connected(self):
        return self.established_connection


    def send_counter(self):
        if not self.established_connection:
            for i in range(5):
                try:
                    self.lock.acquire()
                    if not self.established_connection:
                        msg = f"{self.handler_status.host_username} -> {self.handler_status.player_name}:{self.handler_status.msg_to_send}"
                    else:
                        msg = self.handler_status.msg_to_send
                    self.lock.release()
                    sent = self.conn.send(str(msg).encode())
                    break
                except socket.error:
                    if self.lock.locked():
                        self.lock.release()
                    if i == 5:
                        self.logger.debug("Couldn't send message. Receiver must've closed connection!")
                        self.handler_status.is_connected = "connection_error"
        else:
            self.lock.acquire()
            try:
                msg = self.handler_status.msg_to_send
                self.conn.send(str(msg).encode())
                self.numbers_of_errors = 0
            except socket.error as e:
                self.numbers_of_errors = self.numbers_of_errors + 1
            self.lock.release()

    def get_counter(self):
        if not self.established_connection:
            for i in range(5):
                try:
                    self.lock.acquire()
                    self.handler_status.received_msg = self.conn.recv(2048)
                    self.handler_status.received_msg = self.handler_status.received_msg.decode()
                    self.lock.release()
                    if self.handler_status.received_msg == '':
                        self.logger.debug("Socket connection shut down")
                        self.handler_status.is_connected = "connection_error"
                        self.handler_status.to_kill = True
                        break
                    self.established_connection = True
                    break
                except socket.error:
                    if self.lock.locked():
                        self.lock.release()
                    if i == 5:
                        self.logger.debug("Couldn't receive message. Receiver must've closed connection!")
                        self.handler_status.is_connected = "connection_error"
        else:
            self.lock.acquire()
            try:
                self.handler_status.received_msg = self.conn.recv(2048)
                self.handler_status.received_msg = self.handler_status.received_msg.decode()
                self.numbers_of_errors = 0
            except socket.error as e:
                self.numbers_of_errors = self.numbers_of_errors + 1
            self.lock.release()
        

    def connect(self):
        tries = 0
        self.socket.settimeout(10.0)
        self.logger.debug(f"Trying to connect with: {self.handler_status.player_ip}:{self.handler_status.player_port}")
        while True:
            try:
                self.socket.connect((self.handler_status.player_ip, self.handler_status.player_port))
                self.socket.settimeout(None)
                self.conn = self.socket
                self.logger.debug(f"Connected with: {self.handler_status.player_ip}:{self.handler_status.player_port}")
                self.handler_status.is_connected = "connected"
                return
            except socket.error as msg:
                self.logger.debug(f"Try: {tries}")
                self.logger.debug(f"Couldn't connect: {msg}")
                tries += 1
                if tries > 5:
                    self.socket.close()
                    self.handler_status.is_connected = "connection_error"
                    self.handler_status.to_kill = True
                    return
                time.sleep(1.0)

    def listen(self):
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((self.handler_status.host_ip, self.handler_status.host_port))
        self.socket.settimeout(10.0)
        self.socket.listen(4)
        self.logger.debug(f"Listening on: {self.handler_status.host_ip}:{self.handler_status.host_port}")
        try:
            self.lock.acquire()
            self.conn, (ip, port) = self.socket.accept()
            self.socket.settimeout(None)
            self.lock.release()
            self.logger.debug(f"Someone connected with me from {ip}:{port}")
            self.handler_status.is_connected = "connected"
        except socket.timeout:
            self.handler_status.is_connected = "connection_error"
            self.handler_status.to_kill = True

    def kill(self):
        try:
            self.socket.shutdown(socket.SHUT_RDWR)
            self.socket.close()
        except socket.error:
            # already closed
            pass
        try:
            self.conn.shutdown(socket.SHUT_RDWR)
            self.conn.close()
        except socket.error:
            # already closed
            pass