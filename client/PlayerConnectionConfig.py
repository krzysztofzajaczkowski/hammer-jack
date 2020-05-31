class PlayerConnectionConfig:
    def __init__(self, player_name, player_ip, player_ports):
        self.player_name = player_name
        self.player_ip = player_ip
        self.player_ports = player_ports

    def pretty_print(self):
        print(f"{self.player_name} -> {self.player_ip}:{self.player_ports}")
