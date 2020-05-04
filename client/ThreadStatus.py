class ThreadStatus:
    def __init__(self, host_username, player_name, active_connect, host_ip, host_port,
                 player_ip, player_port):
        self.host_username = host_username
        self.player_name = player_name
        self.is_connected = 0
        self.is_active_connect = active_connect
        self.host_ip = host_ip
        self.host_port = host_port
        self.player_ip = player_ip
        self.player_port = player_port
        self.to_kill = 0
        self.msg = 0