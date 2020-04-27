import socket
import threading
import time
from collections import OrderedDict


class ClientThread(threading.Thread):

    def __init__(self, ip, port, conn: socket.socket, other_users):
        threading.Thread.__init__(self)
        self.conn = conn
        self.ip = ip
        self.port = port
        self.username = ""
        self.other_users = other_users
        self.dead = False
        print("[+] New server socket thread started for " + ip + ":" + str(port))

    def run(self):
        self.first_data()
        try:
            while not self.dead:
                self.conn.settimeout(10.0)
                data = self.conn.recv(2048)
                MESSAGE = str(self.respond(data.decode()))
                self.conn.send(MESSAGE.encode())  # echo
        except (socket.timeout, socket.error):
            self.kill()

    def respond(self, msg):
        switcher = {
            "GAME_STATE": self.queue_status()
        }
        return switcher.get(msg, "DISCONNECT")

    def queue_status(self):
        if len(list(self.other_users)) >= 3:
            pass
            # TODO REMOVE PLAYERS FROM QUEUE AND SEND THEM PORTS/IP
        print(self.other_users)
        return list(self.other_users).index(self.username)

    def first_data(self):
        data = self.conn.recv(2048)
        data = data.decode().split('♞')
        print("Server received data:", data)
        self.username = data[0].strip()
        self.other_users[self.username] = [self.ip, self.port, "waiting"]
        MESSAGE = "Hello! User " + data[0].strip() + " choosed " + data[1].strip()
        self.conn.send(MESSAGE.encode())  # echo

    def kill(self):
        try:
            self.conn.send("DISCONNECT".encode())
            self.conn.shutdown(socket.SHUT_RDWR)
            self.conn.close()
        except OSError:
            pass
        finally:
            if self.username in self.other_users.keys():
                del self.other_users[self.username]
                print("Successfuly deleted player", self.username)
                self.dead = True


class PlayersManager(threading.Thread):
    def __init__(self, other_players):
        super().__init__()
        self.other_players = other_players
        self.dead = False

    def run(self):
        while not self.dead:
            # print(len(self.other_players))
            if len(self.other_players) >= 2:
                print(list(self.other_players)[:2])
            time.sleep(3)

    def kill(self):
        print("Queue down")
        self.dead = True


class Server:
    def __init__(self, port=63300, addr='localhost'):
        self.players = OrderedDict()
        self.tcpServer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.threads = []
        self.ip = addr
        self.port = port
        self.create_tcp()
        self.queue = PlayersManager(self.players)
        self.queue.start()
        self.threads.append(self.queue)
        self.dead = False

    def create_tcp(self):
        self.tcpServer.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.tcpServer.bind((self.ip, self.port))

    def listen(self):
        while not self.dead:
            self.tcpServer.listen(4)
            print("Multithreaded Python server : Waiting for connections from TCP clients...")
            (conn, (ip, port)) = self.tcpServer.accept()
            newthread = ClientThread(ip, port, conn, self.players)
            newthread.start()
            self.threads.append(newthread)

    def die(self):
        for thread in threading.enumerate():
            if thread.getName() != "MainThread":
                try:
                    thread.kill()
                except SystemExit:
                    pass
        try:
            self.dead = True
        except SystemExit:
            print("Main thread down")
            return


def main():
    server = Server()
    try:
        server.listen()
    except KeyboardInterrupt:
        server.die()
    finally:
        for i in threading.enumerate():
            try:
                i.join()
            except RuntimeError:
                pass


if __name__ == '__main__':
    main()
