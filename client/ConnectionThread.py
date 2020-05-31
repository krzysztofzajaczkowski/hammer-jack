import socket
import threading
import time


class ConnectionThread(threading.Thread):
    def __init__(self, thread_status):
        threading.Thread.__init__(self)
        self.handler_status = thread_status
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.conn = None
        self.lock = threading.Lock()

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
            self.conn.settimeout(3.0)
            while not self.handler_status.to_kill:
                self.send_counter()
                time.sleep(1.0)
                self.get_counter()
                self.handler_status.msg += 1
        finally:
            self.kill()

    def send_counter(self):
        self.lock.acquire()
        for i in range(5):
            try:
                msg = f"{self.handler_status.host_username} -> {self.handler_status.player_name}:{self.handler_status.msg}"
                sent = self.conn.send(msg.encode())
                print(f"Sent: {sent}")
                break
            except socket.error:
                if i == 5:
                    print("Couldn't send message. Receiver must've closed connection!")
                    self.handler_status.is_connected = "connection_error"
        self.lock.release()

    def get_counter(self):
        self.lock.acquire()
        for i in range(5):
            try:
                msg = self.conn.recv(2048)
                msg = msg.decode()
                if msg == '' or msg == ' ':
                    print("Socket connection shut down")
                    self.handler_status.is_connected = "connection_error"
                print(msg)
                break
            except socket.error:
                if i == 5:
                    print("Couldn't receive message. Receiver must've closed connection!")
                    self.handler_status.is_connected = "connection_error"
        self.lock.release()

    def connect(self):
        tries = 0
        self.socket.settimeout(10.0)
        print(f"Trying to connect with: {self.handler_status.player_ip}:{self.handler_status.player_port}")
        while True:
            try:
                self.socket.connect((self.handler_status.player_ip, self.handler_status.player_port))
                self.socket.settimeout(None)
                self.conn = self.socket
                print(f"Connected with: {self.handler_status.player_ip}:{self.handler_status.player_port}")
                self.handler_status.is_connected = "connected"
                return
            except socket.error as msg:
                print(f"Try: {tries}")
                print(f"Couldn't connect: {msg}")
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
        print(f"Listening on: {self.handler_status.host_ip}:{self.handler_status.host_port}")
        try:
            self.lock.acquire()
            self.conn, (ip, port) = self.socket.accept()
            self.socket.settimeout(None)
            self.lock.release()
            print(f"Someone connected with me from {ip}:{port}")
            self.handler_status.is_connected = "connected"
        except socket.timeout:
            self.handler_status.is_connected = "connection_error"
            self.handler_status.to_kill = True

    def kill(self):
        try:
            self.socket.shutdown(socket.SHUT_RDWR)
            self.socket.close()
        except socket.error:
            pass
        try:
            self.conn.shutdown(socket.SHUT_RDWR)
            self.conn.close()
        except socket.error:
            pass
