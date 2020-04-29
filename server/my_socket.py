import socket
import threading
import time
from collections import OrderedDict
from random import sample


class ClientThread(threading.Thread):

    def __init__(self, conn: socket.socket, other_users, games):
        threading.Thread.__init__(self)
        self.conn = conn
        self.ip_addr, self.port = conn.getsockname()
        self.username = ""
        self.other_users = other_users
        self.dead = False
        self.games = games
        print("[+] New server socket thread started for " + self.ip_addr + ":" + str(self.port))

    def run(self):
        self.first_data()
        try:
            while not self.dead:
                self.conn.settimeout(10.0)
                data = self.conn.recv(2048)
                print(data.decode())
                message = str(self.respond(data.decode()))
                self.conn.send(message.encode())  # echo
        except (socket.timeout, socket.error):
            self.kill()

    def actual_status(self, who=None, expected_status="forming"):
        if who is None:
            return bool(self.other_users[self.username][2] == expected_status)
        return bool(self.other_users[str(who)][2] == expected_status)

    def respond(self, msg):
        if msg == "GAME_STATE":
            return self.queue_status()
        if msg == "CREATED_GAME":
            return self.change_players_status()
        return "DISCONNECT"

    def queue_status(self):
        if self.actual_status():
            return self.form_game()
        print(self.other_users)
        return [x[0] for x in self.other_users.items() if x[1][2] == "waiting"].index(self.username)

    def change_players_status(self, status_changed_to="created"):
        if status_changed_to == self.actual_status(expected_status=status_changed_to):
            game = self.find_in_which_game()
            for player in game:
                if len(player) == 2:
                    if not self.actual_status(expected_status=status_changed_to, who=player[0]):
                        return "WAIT"
            self.kill()
            return "DISCONNECT"
        self.other_users[self.username][2] = status_changed_to
        return "WAIT"

    def find_in_which_game(self):
        for game in self.games:
            for player in game:
                if player[0] == self.username:
                    return game
        return []

    def form_game(self):
        actual_msg = self.find_in_which_game()
        return str(actual_msg)

    def first_data(self):
        data = self.conn.recv(2048)
        data = data.decode().split('♞')
        print("Server received data:", data)
        self.username = data[0].strip()
        self.other_users[self.username] = [self.ip_addr, self.port, "waiting"]
        message = "Hello! User " + data[0].strip() + " choosed " + data[1].strip()
        self.conn.send(message.encode())  # echo

    def kill(self):
        print("zabijam")
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

    def check_status(self, nickname: str) -> str:
        try:
            return self.other_players.get(nickname)[2]
        except (KeyError, IndexError):
            return "ERROR"

    def count_waiting_players(self, status="waiting") -> int:
        return len([x for x in self.other_players.items() if x[1][2] == status])

    def create_game_variable(self, status="waiting") -> list:
        game = []
        for client in self.other_players.items():
            if len(game) < self.players_per_game:
                if client[1][2] == status:
                    game.append([client[0], client[1][0]])
            else:
                break
        return game

    def change_players_status(self, game: list, status_to_be_changed_to="forming"):
        for player in game:
            self.other_players[player[0]][2] = status_to_be_changed_to

    def run(self):
        while not self.dead:
            if self.count_waiting_players() >= self.players_per_game:
                game = self.create_game_variable()
                if len(game) == self.players_per_game:
                    self.change_players_status(game)
                game.append(sample(range(55000, 56000), 3))
                self.games.append(game)
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
            conn = self.tcp_server.accept()[0]
            new_thread = ClientThread(conn, self.players, self.games)
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
