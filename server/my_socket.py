import socket
import threading
import time
import logging
from collections import OrderedDict
from functools import wraps


class ClientThread(threading.Thread):

    def __init__(self, ip, port, conn: socket.socket, other_users):
        threading.Thread.__init__(self)
        self.conn = conn
        self.ip = ip
        self.port = port
        self.username = ""
        self.other_users = other_users
        print("[+] New server socket thread started for " + ip + ":" + str(port))

    def run(self):
        self.first_data()
        while True:
            data = self.conn.recv(2048)
            data = data.decode().split('♞')
            print("Server received data:", data)
            MESSAGE = "User " + data[0].strip() + " said " + data[1].strip()
            if data[1].strip() == 'leave':
                self.kill()
                break
            self.conn.send(MESSAGE.encode())  # echo

    def first_data(self):
        data = self.conn.recv(2048)
        data = data.decode().split('♞')
        print("Server received data:", data)
        self.username = data[0].strip()
        self.other_users[self.username] = "waiting"
        MESSAGE = "Hello! User " + data[0].strip() + " said " + data[1].strip()
        if MESSAGE == 'leave':
            return
        self.conn.send(MESSAGE.encode())  # echo

    def kill(self):
        self.conn.shutdown(socket.SHUT_RDWR)
        self.conn.close()
        del self.other_users[self.username]


class PlayersManager(threading.Thread):
    def __init__(self, other_players):
        super().__init__()
        self.other_players = other_players

    def run(self):
        while True:
            print(len(self.other_players))
            if len(self.other_players) >= 2:
                print(list(self.other_players)[:2])
            time.sleep(3)


class Server:
    def __init__(self, port=63300, addr='localhost'):
        self.players = OrderedDict()
        self.threads = []
        self.tcpServer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.IP = addr
        self.PORT = port
        self.BUFFER_SIZE = 64
        self.create_tcp()
        self.queue = PlayersManager(self.players)
        self.queue.start()

    def create_tcp(self):
        self.tcpServer.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.tcpServer.bind((self.IP, self.PORT))

    def listen(self):
        while True:
            self.tcpServer.listen(4)
            print("Multithreaded Python server : Waiting for connections from TCP clients...")
            (conn, (ip, port)) = self.tcpServer.accept()
            newthread = ClientThread(ip, port, conn, self.players)
            newthread.start()
            self.threads.append(newthread)


server = Server()
server.listen()
