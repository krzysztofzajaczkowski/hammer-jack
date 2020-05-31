from tkinter import *
from tkinter import messagebox
import threading
from game_logic import Game, GameView
from enum import IntEnum
import math
from time import sleep
from Logger import Logger

# # import tkinter as tk
# # import threading

# class App(threading.Thread):

#     def __init__(self):
#         threading.Thread.__init__(self)
#         self.setDaemon(True)
#         self.root = None
#         self.label_var = None
#         self.start()

#     def callback(self):
#         self.root.quit()

#     def run(self):
#         self.root = Tk()
#         self.root.protocol("WM_DELETE_WINDOW", self.callback)
#         self.label_var = StringVar()

#         label = Label(self.root, textvariable=self.label_var)
#         label.pack()

#         self.root.mainloop()
#         return


# app = App()
# # print('Now we can continue running code while mainloop runs!')

# try:
#     while True:
#         new_label_name = input('Set new label name: ')
#         app.label_var.set(new_label_name)
# except KeyboardInterrupt as e:
#     pass

# # for i in range(5000):
# #     print(i)

# app.callback()

# # app.root.destroy()

RECT_SIZE = 40
KEY_DICT = {
    81: ["Q",0],
    87: ["W",1],
    69: ["E",2],
    65: ["A",3],
    83: ["S",4],
    68: ["D",5],
    90: ["Z",6],
    88: ["X",7],
    67: ["C",8]
}
MOLE_STATUS_COLORS = ["white", "firebrick3", "red", "tomato"]
MOLES_POSITION = [
    [0,0],[1,0],[2,0],
    [0,1],[1,1],[2,1],
    [0,2],[1,2],[2,2],
]
NUMBER_OF_MOLES = 9

class MoleState(IntEnum):
    HIDDEN = 0
    HIDING_2 = 1
    HIDING_1 = 2
    VISIBLE = 3

class PlayerBoard():
    def __init__(self, player_name, root_window):
        self.logger = Logger.get_logger('PlayerBoard')
        # set all data fields
        self.player_name_value = player_name
        self.player_name_format = "Player: {0}"
        self.player_score_value = 0
        self.player_score_format = "Score: {0}"
        self.player_combo_value = 1
        self.player_combo_format = "Combo: {0}"
        self.moles_status = [0] * NUMBER_OF_MOLES
        self.moles_lock = threading.Lock()
        self.disconnected = False
        self.end_game = False
        # initialize StringVars for UI
        self.player_name_stringvar = StringVar()
        self.set_player_name(self.player_name_value)
        #self.player_name_stringvar.set(self.player_name_format.format(self.player_name_value))
        self.player_combo_stringvar = StringVar()
        self.set_player_combo(self.player_combo_value)
        # self.player_combo_stringvar.set(self.player_combo_format.format(self.player_combo_value))
        self.player_score_stringvar = StringVar()
        self.set_player_score(self.player_score_value)
        # self.player_score_stringvar.set(self.player_score_format.format(self.player_score_value))

        # create base layout
        self.top_frame = Frame(root_window)
        self.middle_frame = Frame(root_window)
        # pack layout into root window
        self.top_frame.pack(side=TOP)
        self.middle_frame.pack()

        # create labels
        self.player_name_label = Label(self.top_frame, textvariable=self.player_name_stringvar)
        self.player_combo_label = Label(self.top_frame, textvariable=self.player_combo_stringvar)
        self.player_score_label = Label(self.top_frame, textvariable=self.player_score_stringvar)
        # pack labels in top frame
        self.player_name_label.pack(side=LEFT, padx=5)
        self.player_combo_label.pack(side=LEFT, padx=5)
        self.player_score_label.pack(side=LEFT, padx=5)

        # create canvas
        self.canvas = Canvas(self.middle_frame, width=3*RECT_SIZE+10, height=3*RECT_SIZE+10)
        # pack canvas into middle frame
        self.canvas.pack()
        self.init_board()

    def draw_mole(self, x, y, status):
        if (x and y) in range(int(math.sqrt(NUMBER_OF_MOLES))):
            drawing_start_x = 5+x*(RECT_SIZE)
            drawing_start_y = 5+y*(RECT_SIZE)
            self.canvas.create_rectangle(drawing_start_x, drawing_start_y, drawing_start_x + RECT_SIZE,
                                        drawing_start_y + RECT_SIZE, fill=MOLE_STATUS_COLORS[status])
        else:
            self.logger.debug(f"{x},{y} not in range")

    def draw_board(self):
        for idx, mole_status in enumerate(self.moles_status):
            moles_pos = MOLES_POSITION[idx]
            self.draw_mole(moles_pos[0], moles_pos[1], mole_status)

    def init_board(self):
        '''
            Initialize 3x3 white board on screen
        '''
        for x in range(int(math.sqrt(NUMBER_OF_MOLES))):
            for y in range(int(math.sqrt(NUMBER_OF_MOLES))):
                self.draw_mole(x, y, MoleState.HIDDEN)

    def set_player_name(self, player_name):
        if not self.disconnected:
            self.player_name_value = player_name

    def set_player_score(self, score):
        if not self.disconnected:
            self.player_score_value = score

    def set_player_combo(self, combo):
        if not self.disconnected:
            self.player_combo_value = combo

    def set_moles_status(self, moles_status):
        if not self.disconnected:
            self.moles_status = moles_status

    def update_player_name(self):
        '''
            Update player name with new value or DISCONNECTED if player is disconnected
        '''
        if not self.disconnected:
            self.player_name_stringvar.set(self.player_name_format.format(self.player_name_value))
        else:
            self.player_name_stringvar.set(self.player_name_format.format('DISCONNECTED'))

    def update_player_score(self):
        if not self.disconnected:
            self.player_score_stringvar.set(self.player_score_format.format(self.player_score_value))

    def update_player_combo(self):
        if not self.disconnected:
            self.player_combo_stringvar.set(self.player_combo_format.format(self.player_combo_value))
        

    def set_disconnected(self):
        self.disconnected = True


class App(threading.Thread):
    def __init__(self, main_player_name, players_names):
        super().__init__()
        self.logger = Logger.get_logger('App')
        self.setDaemon(True)
        self.is_screen_destroyed = False
        self.is_end_game = False
        self.game_thread = None
        self.game_views = []
        self.connections_threads = []
        self.main_player_name = main_player_name
        self.players_names = players_names
        self.main_player_board = None
        self.is_running = False
        self.other_players_boards = None
        self.winner = None
        self.start()

    def set_game_thread(self, game_thread):
        self.game_thread = game_thread

    def callback(self):
        self.is_screen_destroyed = True
        self.main_window.quit()

    def keydown_func(self, e):
        '''
            Register keystrokes
        '''
        if self.game_thread is not None:
            pressed_key = e.keycode
            if pressed_key in KEY_DICT.keys():
                self.game_thread.pressed_keys_lock.acquire()
                self.game_thread.pressed_key.append(KEY_DICT[pressed_key][1])
                self.game_thread.pressed_keys_lock.release()

    def update_window(self):
        '''
            Update all boards in window
        '''
        if self.is_screen_destroyed:
            return
        if not self.is_end_game:
            self.main_player_board.update_player_name()
            self.main_player_board.update_player_combo()
            self.main_player_board.update_player_score()
            self.main_player_board.draw_board()
            for player_board in self.other_players_boards:
                player_board.update_player_name()
                player_board.update_player_combo()
                player_board.update_player_score()
                player_board.draw_board()
            self.main_window.after(500, self.update_window)
            


    def run(self):
        # Initialize Tkinter window and layout
        # Pretty much all inline due to tkinter problems with threading
        self.main_window = Tk()
        self.main_window.protocol("WM_DELETE_WINDOW", self.callback)
        self.main_window.geometry("{}x{}".format(700,600))
        self.main_window.title("HammerJack")
        self.main_window.focus_set()
        self.frames = []
        self.other_players_boards = []
        self.all_players_boards = []
        self.main_player_board = None
        for i in range(2):
            for j in range(2):
                frame = Frame(self.main_window)
                frame.grid(row=i, column=j, padx=50, pady=50)
                self.frames.append(frame)
        self.main_player_board = PlayerBoard(self.main_player_name, self.frames[0])
        self.all_players_boards.append(self.main_player_board)
        for idx, player in enumerate(self.players_names):
            board = PlayerBoard(player, self.frames[idx+1])
            self.other_players_boards.append(board)
            self.all_players_boards.append(board)
        self.main_window.bind("<KeyPress>", self.keydown_func)
        self.is_running = True
        self.main_window.after(500, self.update_window)
        self.main_window.mainloop()
    

