from pygomo  import Engine
<<<<<<< Updated upstream
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
=======
from pygomo  import Move
from pygomo  import PlayResult
from utils   import detect_board, detect_opening
from utils   import ScreenCapture
from utils   import check_state, kill_process
from utils   import Listener
from utils   import DataBinding
from typing  import List
import threading
import os

class Model:
    def __init__(self):            
        self.engine     = DataBinding('')
        self.time_match = DataBinding(60)
        self.time_plus  = DataBinding(0)
        self.mode       = DataBinding(False)

        self.__state         : bool   = False    
        self.__engine_exec   : Engine = None
        self.__distance      : int    = None
        self.__board_position: List[int, int, int, int] = None, None, None, None
        

        self.__game_lock = threading.Lock()
        self.__listener  = Listener(max_callback_workers=1, debounce_ms=500)

        self.__listener.add_hotkey('alt+s', self.stop_game)
        self.__listener.add_hotkey('esc'  , self.turn_off)
        self.__listener.add_hotkey('ctrl+shift+x', self.start_game_thread)        

    def load_engine(self):
        assert os.path.exists(engine := self.engine.get())
        self.__engine_exec = Engine(engine, 'gomocup')
        print(f'Loaded: {self.__engine_exec.id}')

    def is_engine_available(self):
        return isinstance(self.__engine_exec, Engine)

    def terminate_engine(self):
        if self.is_engine_available():
            print('[Terminate engine]')
            self.__engine_exec.terminate()
            self.__engine_exec = None

    def safe_kill_engine(self):
        if self.is_engine_available() and check_state(self.__engine_exec.id):
            print('[Safe kill]')
            kill_process(self.__engine_exec.id)

    def detect_board(self, master):
        self.__board_position = detect_board(*ScreenCapture(master).get())
        if all(self.__board_position):
            self.__distance = self.__board_position[2] / 14
            print('Board Position:', self.__board_position)

    def turn_off(self):
        if self.__state:
            self.stop_game()
        self.terminate_engine()

    def turn_on(self):
        assert self.__board_position
        assert self.engine.get()
        assert not self.is_engine_available()
        self.load_engine()

    def stop_game(self):
        self.__state = False

    def start_game_thread(self):
        assert self.is_engine_available()
        assert self.__board_position
        if not self.__state and self.__game_lock.acquire(blocking=False):
            print("Starting game thread...")
            threading.Thread(target=self.start_game, daemon=True).start()
        else:
            print("Game is already running. Ignoring start command.")

    def start_game(self):
        def recursive_get_info():
            while self.__state:
                try:                    
                    # Represent to View
                    best_move = self.__engine_exec._receive('coord')
                    if best_move:
                        message   = PlayResult(None, self.__engine_exec._receive('message', reset=True)).info
                        best_move = Move(best_move)
                        print(f'DEPTH {message["depth"]} | Winrate {message["ev"].winrate() * 100:.2f}% | NODE {message["node"]} | NPS {message["nps"]} | PV {message["pv"]}')                        
                        print('[BestMove]', best_move)
                        return best_move
                except:
                    continue
            
        def recursive_play():
            ...
        try:            
            self.__state = True
            # Logic
            # -----
            assert self.__engine_exec.protocol.is_ready(timeout=self.time_match.get()), 'Engine is not ready'
            self.__engine_exec.protocol.configure({
                'timeout_match': self.time_match.get() * 1000,
                'time_left'    : self.time_match.get() * 1000,
                'rule'         : 1
            })
            while self.__state:
                # STEP 1: Receive opening
                opening = detect_opening(*self.__board_position, self.__distance)
                # STEP 2: Send to Engine
                print('Opening:', opening)
                moves_str = "\n".join([f"{move[0]},{move[1]},{1 if len(opening) % 2 == idx % 2 else 2}" for idx, move in enumerate(opening)])
                self.__engine_exec.protocol.send_command(f'board\n{moves_str}\ndone')
                # Step 3: Represent
                output = recursive_get_info()
                break
                # Step 4: Local update time
                recursive_play()
            print('break')
        finally:
            self.__state = False
            self.__game_lock.release()
>>>>>>> Stashed changes
