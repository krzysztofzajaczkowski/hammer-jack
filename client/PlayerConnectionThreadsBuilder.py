from PlayerConnectionConfig import PlayerConnectionConfig
from ThreadStatus import ThreadStatus
from ConnectionThread import ConnectionThread
from PlayerConnectionThreadHandler import PlayerConnectionThreadHandler


class PlayerConnectionThreadsBuilder:
    def __init__(self):
        self.username = None
        self.users = None
        self.ports = None
        self.client_index = None
        self.client_configs = None
        self.other_players_configs = None
        self.number_of_active_connections = None
        self.client_to_ports_config = None

    def convert_server_response_to_users_and_ports(self, response):
        '''Split response to users list and ports list'''
        self.users = response[:-1]
        self.ports = response[-1]

    def find_client_index_in_users(self, username):
        '''Find current client's index in users list'''
        self.username = username
        if self.users is not None:
            for i in range(len(self.users)):
                if self.users[i][0] == username:
                    self.client_index = i
                    return
        else:
            print('self.users is needed!')

    def prepare_connection_config_for_each_player(self):
        '''Create config for each player with their IP and ports'''
        if self.username is not None and \
                self.users is not None and \
                self.ports is not None:
            self.client_configs = []
            self.other_players_configs = []
            for i in range(len(self.users)):
                user_ports = self.ports[i * (len(self.users)):(i + 1) * (len(self.users))]
                player_config = PlayerConnectionConfig(self.users[i][0], self.users[i][1], user_ports)
                self.client_configs.append(player_config)
                if self.users[i][0] != self.username:
                    self.other_players_configs.append(player_config)
        else:
            print('username, users and ports are needed!')

    def get_number_of_active_connections(self):
        '''Get how many connections should be created actively(client connects, rather than listens)'''
        if self.users is not None and \
                self.client_index is not None:
            self.number_of_active_connections = int(len(self.users) / 2 - 1) if self.client_index >= len(
                self.users) / 2 and len(
                self.users) / 2 % 2 == 0 else int(len(self.users) / 2)
        else:
            print('self.users and self.client_index are needed!')

    def prepare_client_connections_config(self):
        '''Prepare connection config for each player client should connect to (username, ip, port, mode[active/passive])'''
        if self.client_configs is not None and \
                self.other_players_configs is not None and \
                self.client_index is not None and \
                self.number_of_active_connections is not None:
            self.client_to_ports_config = []
            for i in range(len(self.client_configs)):
                if i != self.client_index:
                    self.client_to_ports_config.append(
                        [self.client_configs[self.client_index].player_ports[i], "passive",
                         self.client_configs[i].player_name, self.client_configs[i].player_ip])
            for i in range(self.number_of_active_connections):
                index = self.client_index + i
                if index >= len(self.client_to_ports_config):
                    index -= len(self.client_to_ports_config)
                self.client_to_ports_config[index][1] = "active"
                self.client_to_ports_config[index][0] = self.other_players_configs[index].player_ports[
                    self.client_index]
        else:
            print('client_configs and other_players_configs and client_index'
                  ' and number_of_active_connections are neeeded!')

    def build(self):
        '''Build handlerStatuses and threads for each connection'''
        if self.client_to_ports_config is not None and self.username is not None:
            player_connections = []
            for config in self.client_to_ports_config:
                is_active_connect = 0
                host_port = None
                player_port = None
                if config[1] == "active":
                    is_active_connect = 1
                    player_port = config[0]
                else:
                    host_port = config[0]
                thread_status = ThreadStatus(self.username, config[2], is_active_connect, 'localhost',
                                             host_port, config[3], player_port)
                thread = ConnectionThread(thread_status)
                player_connection = PlayerConnectionThreadHandler(thread, thread_status)
                player_connections.append(player_connection)
            return player_connections
        else:
            print('client_to_ports_config and username are needed!')