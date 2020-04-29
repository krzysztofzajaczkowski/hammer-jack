import socket
import threading
import time
from collections import OrderedDict


class ClientThread(threading.Thread):

    def __init__(self, ip, port, conn: socket.socket, other_users):
        threading.Thread.__init__(self)
        self.conn = conn
        self.ip_addr = ip
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
                message = str(self.respond(data.decode()))
                self.conn.send(message.encode())  # echo
        except (socket.timeout, socket.error):
            self.kill()

    def respond(self, msg):
        switcher = {
            "GAME_STATE": self.queue_status()
        }
        return switcher.get(msg, "DISCONNECT")

    def queue_status(self):
        if len(list(self.other_users)) >= 3 and self.other_users[self.username][2] == "ingame":
            return self.form_game()
        print(self.other_users)
        return list(self.other_users).index(self.username)

    def form_game(self):
        pass

    def first_data(self):
        data = self.conn.recv(2048)
        data = data.decode().split('♞')
        print("Server received data:", data)
        self.username = data[0].strip()
        self.other_users[self.username] = [self.ip_addr, self.port, "waiting"]
        message = "Hello! User " + data[0].strip() + " choosed " + data[1].strip()
        self.conn.send(message.encode())  # echo

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
    def __init__(self, other_players, active_games):
        super().__init__()
        self.other_players = other_players
        self.games = active_games
        self.dead = False
        self.players_per_game = 3

    def run(self):
        while not self.dead:
            print(len(self.other_players))
            print(threading.enumerate())
            if len(self.other_players) >= self.players_per_game:
                pass
                # print(list(self.other_players)[:players_in_single_game])
                # game = self.other_players[:players_in_single_game]
                # for player in list(game):
                #     self.other_players[player][2] = "ingame"
                # self.games.append(game)
            time.sleep(3)

    def kill(self):
        print("Queue down")
        self.dead = True


class Server:
    def __init__(self, port=63300, addr='localhost'):
        self.ip_addr = addr
        self.port = port
        self.players = OrderedDict()
        self.tcp_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.games = []
        self.create_tcp()
        self.queue = PlayersManager(self.players, self.games)
        self.queue.start()
        self.dead = False

    def create_tcp(self):
        self.tcp_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.tcp_server.bind((self.ip_addr, self.port))

    def listen(self):
        while not self.dead:
            self.tcp_server.listen(4)
            print("Multithreaded Python server : Waiting for connections from TCP clients...")
            (conn, (ip_addr, port)) = self.tcp_server.accept()
            new_thread = ClientThread(ip_addr, port, conn, self.players)
            new_thread.start()

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

    def new_game(self, single_game):
        self.games.append(single_game)


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
