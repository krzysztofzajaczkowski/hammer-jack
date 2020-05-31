import math
import random
import threading
import time
from itertools import accumulate

MAX_SCORE = 100


class Game(threading.Thread):
    def __init__(self, pressed_keys: list, pressed_keys_lock: threading.Lock):
        super().__init__()
        self.pressed_key = pressed_keys
        self.pressed_keys_lock = pressed_keys_lock
        self.package_number = 0
        self.score = 0
        self.combo = 1
        self.number_of_moles = 9
        self.values_changed = False
        self.mole_life_time = [2, 3]
        self.max_moles_amount = 3
        self.last_print_time = 0
        self.moles_status = [[0, [0, 0, 0]]
                             for _ in range(self.number_of_moles)]  # [status, alive_time]
        self.moles_lock = threading.Lock()
        self.end = False

    def get_score(self) -> str:
        while self.moles_lock.locked():
            time.sleep(0.05)
        return str(self.score)

    def get_combo(self) -> str:
        while self.moles_lock.locked():
            time.sleep(0.05)
        return str(self.combo)

    def get_end(self) -> bool:
        return bool(self.end)

    def get_board(self) -> list:
        while self.moles_lock.locked():
            time.sleep(0.05)
        return [x[0] for x in self.moles_status]

    def run(self):
        self.last_print_time = time.time()
        try:
            while not self.end:
                self.whack_moles()
                self.generate_new_moles()
                self.moles_progression()
                if self.values_changed and self.last_print_time + 1 < time.time():
                    self.package_number += 1
                    self.last_print_time = time.time()
                    if self.score >= MAX_SCORE:
                        self.end = True
                time.sleep(0.2)
        except KeyboardInterrupt:
            return

    def generate_mole_lifetime(self) -> list:
        value = random.uniform(self.mole_life_time[0], self.mole_life_time[1])
        return [time.time() + value * (x + 1) / 3 for x in range(3)]

    def set_new_mole(self, pos: int):
        self.moles_status[pos] = [3, self.generate_mole_lifetime()]

    def hide_mole(self, pos: int):
        self.moles_status[pos] = [0, [0, 0, 0]]

    def moles_progression(self):
        self.moles_lock.acquire()
        op_start_time = time.time()
        for idx, mole in enumerate(self.moles_status):
            for state, checked_time in enumerate(mole[1][::-1]):
                if checked_time < op_start_time:
                    if state != 0:
                        self.moles_status[idx][0] = state
                    else:
                        self.moles_status[idx] = [0, [0, 0, 0]]
                    self.values_changed = True
                    break
        self.moles_lock.release()

    def generate_new_moles(self):
        self.moles_lock.acquire()
        while sum([bool(x[0]) for x in self.moles_status]) < self.max_moles_amount:
            rand = random.random()
            if self.moles_status[int(rand * self.number_of_moles)][0] == 0:
                self.set_new_mole(int(rand * self.number_of_moles))
                self.values_changed = True
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
            self.values_changed = True
            self.calculate_score(key)
        self.moles_lock.release()

    def calculate_score(self, key: int, max_combo=8):
        if self.moles_status[key][0] != 0:
            self.score += self.combo
            self.combo *= 2 if self.combo < max_combo else 1
            self.hide_mole(key)
        else:
            self.combo = 1

    def create_bits_package(self) -> str:
        self.moles_lock.acquire()
        bit_parts = [self.bit_msg_id,
                     self.bit_board,
                     self.bit_combo,
                     self.bit_score,
                     self.bit_state]
        self.moles_lock.release()
        return ''.join([x.__call__() for x in bit_parts])

    def bit_score(self) -> str:
        return bin(self.score)[2:].zfill(8)

    def bit_combo(self) -> str:
        return bin(int(math.log2(self.combo)))[2:].zfill(2)

    def bit_board(self) -> str:
        return ''.join([bin(x[0])[2:].zfill(2) for x in self.moles_status])

    def bit_state(self) -> str:
        return str(int(self.end)).zfill(2)

    def bit_msg_id(self) -> str:
        return (bin(self.package_number % (2 ** 10 - 1))[2:]).zfill(10)


class GameView(threading.Thread):
    def __init__(self):
        super().__init__()
        self.loading_lock = threading.Lock()
        self.actual_counter = 0
        self.package_change = False
        self.end = False
        self.idx = 0
        self.package_parsed = []
        self.package_bin = ''
        self.combo_score = [0, 1]
        self.board = [0 for _ in range(9)]

    def set_package(self, package: str):
        try:
            self.loading_lock.acquire()
            if len(package) > 0:
                self.package_bin = package
                self.package_change = True
        except KeyboardInterrupt:
            print("ERROR!")
            raise SystemExit
        finally:
            self.loading_lock.release()

    def get_score(self) -> str:
        while self.loading_lock.locked():
            time.sleep(0.05)
        return str(self.combo_score[1])

    def get_combo(self) -> str:
        while self.loading_lock.locked():
            time.sleep(0.05)
        return str(self.combo_score[0])

    def get_end(self) -> bool:
        while self.loading_lock.locked():
            time.sleep(0.05)
        return bool(self.end)

    def get_board(self) -> list:
        while self.loading_lock.locked():
            time.sleep(0.05)
        return self.board

    def run(self) -> None:
        while not self.end:
            if self.package_change:
                self.read_package()
                self.package_change = False
            time.sleep(0.05)

    def read_package(self) -> bool:
        self.loading_lock.acquire()
        self.package_parsed = self.split_package()
        if self.valid_counter(int(self.package_parsed[0], 2)):
            self.load_combo_score()
            self.load_board()
            self.load_state()
            self.loading_lock.release()
            return True
        self.loading_lock.release()
        return False

    def split_package(self) -> list:
        lengths = [0, 10, 18, 2, 8, 2]  # [ID, BOARD, COMBO, SCORE, STATE]
        lengths = list(accumulate(lengths))
        return [str(self.package_bin)[lengths[x]: lengths[x + 1]] for x in range(len(lengths) - 1)]

    def valid_counter(self, cnt: int) -> bool:
        if cnt > self.actual_counter or self.actual_counter - cnt > 100:
            self.actual_counter = cnt
            return True
        return False

    def load_board(self):
        self.board = [int(self.package_parsed[1][x * 2:(x + 1) * 2], 2) for x in range(9)]

    def load_combo_score(self):
        if self.check_if_legit():
            self.combo_score = [2 ** (int(self.package_parsed[2], 2)), int(self.package_parsed[3], 2)]
        else:
            print("Cheater!")
            self.end = True

    def check_if_legit(self):
        if int(self.package_parsed[3], 2) - self.combo_score[1] \
                > max(int(self.package_parsed[2], 2), self.combo_score[0]) * max(3, sum([bool(x) for x in self.board])):
            return False
        return True

    def load_state(self):
        if self.package_parsed[4] == '01':
            self.end = True

