from pygomo  import Engine
from pygomo  import Move
from pygomo  import PlayResult
from utils   import detect_board, detect_opening, detect_move
from utils   import ScreenCapture
from utils   import check_state, kill_process
from utils   import Listener
from utils   import DataBinding
from utils   import LogText
from utils   import Board
from utils   import convert_time
from typing  import List
import threading
import os
import time
import keyboard

class Model:
    def __init__(self):            
        self.engine     = DataBinding('')
        self.time_match = DataBinding(60)
        self.time_plus  = DataBinding(0)
        self.mode       = DataBinding(True)
        self.text_box   = LogText()

        self.__state         : bool   = False    
        self.__engine_exec   : Engine = None
        self.__distance      : int    = None
        self.__board         : Board  = None
        self.__board_position: List[int, int, int, int] = None, None, None, None
        
        

        self.__game_lock = threading.Lock()
        self.__listener  = Listener(max_callback_workers=1, debounce_ms=500)

        self.__listener.add_hotkey('alt+s', self.stop_game)
        self.__listener.add_hotkey('esc'  , self.turn_off)
        self.__listener.add_hotkey('ctrl+shift+x', self.start_game_thread)      
        self.__listener.add_hotkey('alt+r', self.text_box.clear)  
        self.__listener.add_hotkey('alt+d', self.__display_search_info)
        self.__listener.add_hotkey('alt+q', self.__stop_engine_search)

    def load_engine(self):
        assert os.path.exists(engine := self.engine.get())
        self.__engine_exec = Engine(engine, 'gomocup')
        print(f'Loaded: {self.__engine_exec.id}')

    def is_engine_available(self):
        return isinstance(self.__engine_exec, Engine)

    def terminate_engine(self):
        if self.is_engine_available():
            self.text_box.set('[Terminate engine]')
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
            self.__board    = Board((self.__board_position[0], self.__board_position[1]), 
                                    (self.__board_position[2], self.__board_position[3]), 
                                    15, 15)
            self.text_box.set('Found board')
            return
        self.text_box.set('No board found')

    def turn_off(self):
        if self.__state:
            self.stop_game()
        self.terminate_engine()

    def turn_on(self):
        assert self.__board_position
        assert self.engine.get()
        assert not self.is_engine_available()
        self.text_box.set('Turned on')
        self.load_engine()

    def stop_game(self):
        self.__state = False

    def start_game_thread(self):
        assert self.is_engine_available()
        assert self.__board_position
        assert self.__board
        if not self.__state and self.__game_lock.acquire(blocking=False):
            self.text_box.set("Starting game thread...")
            threading.Thread(target=self.start_game, daemon=True).start()
        else:
            self.text_box.set("Cannot start game thread...")
            return
    
    def __display_search_info(self, reset=False):
        message = PlayResult(None, self.__engine_exec._receive('message', reset=reset)).info
        self.text_box.set(f'DEPTH {message["depth"]} | Winrate {message["ev"].winrate() * 100:.2f}% | NODE {message["node"]} | NPS {message["nps"]} | PV {message["pv"][:5]}...') 

    def __stop_engine_search(self):
        self.__engine_exec.protocol.stop()

    def start_game(self, recursive=True):
        def click(*coord):
            # Check auto mode
            if self.mode.get():
                self.__board.click(*coord)
            else:
                self.text_box.set('Wait key: ALT + M to continue!')
                keyboard.wait('alt+m')
                self.__board.click(*coord)

        def calc_time_left(begin_at, during):
            return int(begin_at - during + self.time_plus.get()) * 1000
        
        def recursive_get_info() -> Move:
            while self.__state:
                try:                    
                    # Represent to View
                    best_move = self.__engine_exec._receive('coord')
                    if best_move:
                        best_move = Move(best_move)
                        self.__display_search_info(reset=True)              
                        self.text_box.set('[BestMove]', best_move.to_alphabet())
                        return best_move
                except:
                    continue
            
        def recursive_play(begin_time: int, cur_move: List[int]):
            while self.__state:
                try:
                    # Step 1: Set time_left
                    time_start = time.perf_counter()
                    self.__engine_exec.protocol.configure({'time_left': begin_time})

                    # Step 2: Get move || Manage by turn
                    if (move := detect_move(*self.__board_position, self.__distance)) is not None and \
                        move != cur_move:
                        # Step 3: Send to engine
                        move     = Move(move)
                        # FIX BUG ABOUT TIME
                        self.text_box.clear()
                        self.text_box.set(f'--> Time Left: {convert_time(begin_time / 1000)}')

                        self.__engine_exec.protocol.send_command('turn', move.to_strnum())

                        # Step 4: Display & click
                        output   = recursive_get_info()
                        cur_move = output.to_num()      # ,--- Update curmove, advoid duplicate
                        if output is not None:
                            click(*self.__board.move_to_coord(*output.to_num()))

                        # Step 5: Update time_left

                        time_end   = time.perf_counter()
                        begin_time = calc_time_left(begin_time / 1000, time_end - time_start)
                except:
                    continue
        

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
            time_start = time.perf_counter()
            # STEP 1: Receive opening
            opening    = detect_opening(*self.__board_position, self.__distance)

            # STEP 2: Send to Engine
            moves_str  = "\n".join([f"{move[0]},{move[1]},{1 if len(opening) % 2 == idx % 2 else 2}" for idx, move in enumerate(opening)])
            self.__engine_exec.protocol.send_command(f'board\n{moves_str}\ndone')

            # Step 3: Represent
            output     = recursive_get_info()
            if output is not None:
                click(*self.__board.move_to_coord(*output.to_num()))

            # Step 4: Local update time
            time_end   = time.perf_counter()
            time_left  = calc_time_left(self.time_match.get(), time_end - time_start)
            if recursive:
                recursive_play(time_left, output.to_num())
        finally:
            self.__state = False
            self.__game_lock.release()