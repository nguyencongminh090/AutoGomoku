from pygomo  import Engine
from utils   import detect_board, ScreenCapture
from typing  import List

class Model:
    def __init__(self):
        self.engine     = None
        self.time_match = 0
        self.time_plus  = 0
        self.mode       = True

        self.__board_position: List[int, int, int, int] = None, None, None, None

    def load_engine(self, fn: str):
        self.engine = Engine(fn)

    def terminate_engine(self):
        if self.engine is not None:
            self.engine.terminate()

    def detect_board(self, master):
        self.__board_position = detect_board(*ScreenCapture(master).get())
        print('Board Position:', self.__board_position)

    def stop_play(self):
        ...

    def start_play(self):
        ...