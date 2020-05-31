import yaml
import socket
import time
import ast
from PlayerConnectionThreadsBuilder import PlayerConnectionThreadsBuilder
from App import App
from game_logic import Game, GameView
import threading
from tkinter import *
from time import sleep
from PlayerHandler import PlayerHandler
from Logger import Logger

class Client(object):
    def __init__(self, username):
        with open("appsettings.yaml", "r") as config_file:
            config = yaml.safe_load(config_file)
            server_credentials = config['ServerCredentials']
            self.server_address = server_credentials['Address']
            self.server_port = server_credentials['Port']
        self.username = username
        self.connections_threads = None
        self.logger = Logger.get_logger('Client')

    def connect(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.server_address, self.server_port))
            return 0
        except socket.error as msg:
            self.logger.debug(f'Couldn\'t connect: {msg}')
            self.socket.close()
            return -1

    def join_queue(self):
        message = f"{self.username}♞GAME_STATE"
        self.socket.send(message.encode())
        data = self.socket.recv(2048)
        data = data.decode()
        try:
            # first response is a greeting
            self.logger.debug(data)
            # if data is int, then it's a place in queue
            print("Press CTRL + C to leave")
            self.wait_in_queue()
        except ValueError:
            # if data is not int, then we're not in queue
            self.logger.debug("Couldn't join queue...")
            self.socket.shutdown(socket.SHUT_RDWR)
            self.socket.close()

    def handle_threads(self):
        try:
            is_everyone_disconnected = False

            all_players_connected = False

            sleep(2)

            connected_players = 0
            for _ in range(5):
                connected_players = 0
                for conn_thread in self.connections_threads:
                    if conn_thread.thread.is_connected():
                        connected_players = connected_players + 1
                        is_everyone_disconnected = False
                sleep(0.5)
                all_players_connected = connected_players == len(self.connections_threads)
                if all_players_connected:
                    break
            

            if all_players_connected:
                players_names = []

                # clear all message bins
                for conn_thread in self.connections_threads:
                    self.logger.debug(conn_thread.status.player_name)
                    conn_thread.status.msg_to_send = ''
                    conn_thread.status.received_msg = ''
                    players_names.append(conn_thread.status.player_name)

                app = App(self.username, players_names)

                # initialize list and lock for keyPress event
                pressed_keys_list = []
                pressed_keys_lock = threading.Lock()

                main_game = Game(pressed_keys_list, pressed_keys_lock)
                app.set_game_thread(main_game)

                # wait for app to bootstrap
                while not app.is_running:
                    pass

                # initialize players handlers for easier access to board/game_view/connection_thread
                players_handlers = []
                for idx, player_board in enumerate(app.other_players_boards):
                    game_view = GameView(player_board.player_name_value)
                    player_handler = PlayerHandler(player_board, game_view, self.connections_threads[idx])
                    players_handlers.append(player_handler)

                # make handlers immutable
                players_handlers = tuple(players_handlers)

                # start all game threads
                for player in players_handlers:
                    player.game_view.start()
                main_game.start()

                # while not app.is_screen_destroyed and not app.is_end_game:
                end_game = False
                game_view_end = False
                while not app.is_screen_destroyed and not app.is_end_game:
                    if end_game:
                        break
                    # set new values on host board
                    app.main_player_board.set_player_combo(main_game.get_combo())
                    app.main_player_board.set_player_score(main_game.get_score())
                    app.main_player_board.set_moles_status(main_game.get_board())
                    # get new package to send to other players
                    package = main_game.create_bits_package()
                    for conn_thread in self.connections_threads:
                        # set package to send
                        conn_thread.thread.set_message_to_send(package)
                    for idx, player in enumerate(players_handlers):
                        if player.connection_thread.thread.disconnected:
                            player.board.disconnected = True
                        # set received package in game_view for view update
                        player.game_view.set_package(player.connection_thread.thread.get_received_message())
                        player.board.set_player_combo(player.game_view.get_combo())
                        player.board.set_player_score(player.game_view.get_score())
                        player.board.set_moles_status(player.game_view.get_board())
                        if player.game_view.get_end():
                            # set if any of game views has end_state
                            game_view_end = True
                    if main_game.get_end() or game_view_end:
                        # if any game has ended, wait until all players know about endgame
                        end_game = True
                        if not main_game.get_end():
                            main_game.set_end()
                        for idx, player in enumerate(players_handlers):
                            if not player.connection_thread.thread.disconnected:
                                # await only connected players
                                if not player.game_view.get_end():
                                    end_game = False

                # close GUI after ending game
                # after that, App thread automatically shuts down
                app.callback()
                if end_game:
                    # Get the scoreboard
                    players_scores = []
                    players_scores.append([self.username, int(main_game.get_score())])
                    for idx, player in enumerate(players_handlers):
                        players_scores.append([player.board.player_name_value, int(player.game_view.get_score())])
                    players_scores.sort(key=lambda x:x[1], reverse=True)
                    print('---- Scoreboard ----')
                    for idx, player_score in enumerate(players_scores):
                        print(f'{idx+1}. {player_score[0]} - {player_score[1]}')
                    print('---- Scoreboard ----')
                else:
                    print('Disconnected!')

                
                
                # independent of errors in app mainloop - set all games to end, so threads can be closed
                main_game.end = True
                for player in players_handlers:
                    player.game_view.end = True

                # kill all connections
                for connection_thread in self.connections_threads:
                    connection_thread.status.to_kill = True

                # close all threads
                self.logger.debug('Joining main_game')
                app.join()
                main_game.join()
                for player in players_handlers:
                    self.logger.debug(f'Joining {player.board.player_name_value} game_view')
                    player.game_view.join()
                    self.logger.debug(f'Joining {player.board.player_name_value} conn_thread')
                    player.connection_thread.thread.join()
                return
            else:
                print('There were some problems with connection. Shutdown...')
            for connection_thread in self.connections_threads:
                    connection_thread.status.to_kill = True
            for connection_thread in self.connections_threads:
                    connection_thread.thread.join()

        except KeyboardInterrupt as e:
            self.logger.debug('Interrupt in Client')
            self.logger.debug(e)
        

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
                        self.logger.debug(f"Response from server: {data}")
                        # prepare to connect with others
                        self.build_connections_threads(data)
                        self.start_connection_threads()
                        self.handle_threads()
                        break
                    except ValueError:
                        # if not list, then server closed connection
                        self.logger.debug("Server closed connection")
                        self.socket.close()
                        break
                time.sleep(1.0)
        except KeyboardInterrupt:
            print("\nLeaving queue")
            message = f"{self.username}♞LEAVE_QUEUE"
            self.socket.send(message.encode())
            self.socket.shutdown(socket.SHUT_RDWR)
            self.socket.close()
        try:
            self.socket.shutdown(socket.SHUT_RDWR)
            self.socket.close()
        except socket.error:
            pass
        self.socket.close()
