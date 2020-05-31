class PlayerHandler:
    def __init__(self, player_board, game_view, connection_thread):
        self.board = player_board
        self.game_view = game_view
        self.connection_thread = connection_thread