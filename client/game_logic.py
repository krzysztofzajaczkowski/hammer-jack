import threading
import time
import math
import random


class Game(threading.Thread):
    def __init__(self, is_player: bool, pressed_keys: list, pressed_keys_lock: threading.Lock):
        super().__init__()
        self.is_player = is_player
        self.pressed_key = pressed_keys
        self.pressed_keys_lock = pressed_keys_lock
        self.score = 0
        self.combo = 1
        self.number_of_moles = 9
        self.mole_life_time = [1, 3]
        self.max_moles_amount = 3
        self.last_print_time = 0
        self.moles_status = [[0, 0]] * self.number_of_moles  # [status, alive_time]
        self.moles_lock = threading.Lock()
        self.end = False

    def run(self):
        self.last_print_time = time.time()
        try:
            while not self.end:
                self.whack_moles()
                self.generate_new_moles()
                self.moles_progression()
                self.print_board()
                time.sleep(0.2)
        except KeyboardInterrupt:
            return

    def set_new_mole(self, pos: int):
        self.moles_status[pos] = [1, time.time() + random.uniform(self.mole_life_time[0], self.mole_life_time[1])]

    def hide_mole(self, pos: int):
        self.moles_status[pos] = [0, 0]

    def moles_progression(self):
        self.moles_lock.acquire()
        for idx, mole in enumerate(self.moles_status):
            if mole[1] < time.time():
                self.moles_status[idx] = [0, 0]
        self.moles_lock.release()

    def generate_new_moles(self):
        self.moles_lock.acquire()
        while sum([bool(x[0]) for x in self.moles_status]) < self.max_moles_amount:
            rand = random.random()
            if sum(self.moles_status[int(rand * self.number_of_moles)]) == 0:
                self.set_new_mole(int(rand * self.number_of_moles))
        self.moles_lock.release()

    def whack_moles(self):
        self.pressed_keys_lock.acquire()
        unique_keys = []
        for key in self.pressed_key:
            if key not in unique_keys:
                unique_keys.append(key)
        self.pressed_key = []
        self.pressed_keys_lock.release()
        self.moles_lock.acquire()
        for key in unique_keys:
            self.calculate_score(key)
        self.moles_lock.release()

    def calculate_score(self, key: int, max_combo=8):
        if sum(self.moles_status[key]) != 0:
            self.score += self.combo
            self.combo *= 2 if self.combo < max_combo else 1
            self.hide_mole(key)
        else:
            self.combo = 1

    def print_board(self):
        if self.last_print_time + 1 < time.time():
            row_length = int(math.sqrt(self.number_of_moles))
            for idx in range(row_length):
                print("\t".join([str(x[0]) for x in
                                 self.moles_status[idx * row_length:(idx + 1) * row_length]]))
            print("\n")
            self.last_print_time = time.time()

    def create_bits_package(self):
        pass
