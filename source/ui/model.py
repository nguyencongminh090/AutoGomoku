import threading
import os
import time
from typing  import List
import tomllib

import keyboard

from pygomo  import Engine
from pygomo  import Move
from pygomo  import PlayResult
from utils   import detect_board, detect_opening, detect_move, display
from utils   import MoveStack
from utils   import ScreenCapture
from utils   import check_state, kill_process
from utils   import Listener
from utils   import DataBinding
from utils   import LogText
from utils   import Board
from utils   import convert_time


with open('tool_config.toml', 'rb') as f:
    config = tomllib.load(f)


class Model:
    def __init__(self):
        """Initialize the backend model for the Gomoku game automation.
        
        Sets up data bindings, threading locks, hotkey listeners, and initializes
        the game state. Creates hotkey bindings for game control operations.
        """

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
        """Load and initialize the Gomoku engine.
        
        Creates an Engine instance from the configured engine path and establishes
        communication using the 'gomocup' protocol.
        
        Raises:
            AssertionError: If the engine file does not exist.
            Exception: If engine initialization fails.
        """

        assert os.path.exists(engine := self.engine.get())
        self.__engine_exec = Engine(engine, 'gomocup')
        print(f'Engine PID: {self.__engine_exec.id}')

    def is_engine_available(self):
        """Check if the engine is loaded and available.
        
        Returns:
            bool: True if engine is properly initialized, False otherwise.
        """

        return isinstance(self.__engine_exec, Engine)

    def terminate_engine(self) -> bool:
        """Terminate the currently running engine.
        
        Safely shuts down the engine process and cleans up resources.
        
        Returns:
            bool: True if engine was terminated successfully, False if no engine was running.
        """

        if self.is_engine_available():
            self.text_box.set('[Terminate engine]')
            self.__engine_exec.terminate()
            self.__engine_exec = None
            return True
        return False

    def safe_kill_engine(self):
        """Force kill the engine process if it's still running.
        
        Used as a fallback when normal termination fails. Checks if the engine
        process is still active and forcefully terminates it.
        """

        if self.is_engine_available() and check_state(self.__engine_exec.id):
            print('[Safe kill]')
            kill_process(self.__engine_exec.id)

    def detect_board(self, master):
        """Detect and locate the game board on screen.
        
        Captures the screen and attempts to identify the Gomoku board position.
        If successful, initializes the board object and calculates grid spacing.
        
        Args:
            master: The master window/widget for screen capture context.
            
        Side Effects:
            - Updates self.__board_position with detected coordinates
            - Creates self.__board object if detection succeeds
            - Calculates self.__distance for grid spacing
            - Updates UI text with detection status
        """

        self.__board_position = detect_board(*ScreenCapture(master).get())
        if all(self.__board_position):
            self.__distance = self.__board_position[2] / 14
            self.__board    = Board((self.__board_position[0], self.__board_position[1]),
                                    (self.__board_position[2], self.__board_position[3]),
                                    15, 15)
            self.text_box.set('Found board')
            if config['debug_board']:
                display(self.__board_position, 'Board Detect | Display in 5s')
            return
        self.text_box.set('No board found')

    def turn_off(self):
        """Turn off the game automation system.
        
        Stops any running game and terminates the engine. This is a cleanup
        method typically called when shutting down the application.
        """

        if self.__state:
            self.stop_game()
        if self.terminate_engine():
            self.text_box.set('Turned off')

    def turn_on(self):
        """Turn on the game automation system.
        
        Validates prerequisites and loads the engine. Must be called after
        board detection and engine configuration.
        
        Raises:
            AssertionError: If board position not detected, engine not configured,
                            or engine already running.
        """

        assert self.__board_position
        assert self.engine.get()
        assert not self.is_engine_available()
        self.text_box.set('Turned on')
        self.load_engine()

    def stop_game(self):
        """Stop the currently running game.
        
        Sets the game state to stopped, which will cause the game loop to exit
        gracefully at the next iteration.
        """

        if self.__state:
            self.__state = False
            self.text_box.set('Stop Playing')

    def start_game_thread(self):
        """Start a new game in a separate thread.
        
        Creates a daemon thread to run the game loop. Uses thread locking to
        ensure only one game can run at a time.
        
        Raises:
            AssertionError: If engine not available, board not detected, or
                            board object not initialized.
        """

        assert self.is_engine_available()
        assert self.__board_position
        assert self.__board
        with self.__game_lock:
            if not self.__state:
                self.text_box.set("Starting game thread...")
                threading.Thread(target=self.start_game, daemon=True).start()
            else:
                self.text_box.set(f"Cannot start game thread... [game_state={self.__state}]")
                return
    
    def __display_search_info(self, reset=False):
        """Display current engine search information.
        
        Retrieves and formats engine analysis data including search depth,
        win rate, node count, and principal variation.
        
        Args:
            reset (bool, optional): Whether to reset the message buffer. 
                                    Defaults to False.
        """
        
        message = PlayResult(None, self.__engine_exec._receive('message', reset=reset)).info
        self.text_box.set(f'DEPTH {message["depth"]} | '
                          f'Winrate {message["ev"].winrate() * 100:.2f}% | '
                          f'NODE {message["node"]} | '
                          f'NPS {message["nps"]} | '
                          f'PV {" ".join(map(str, message["pv"][:5]))}...')

    def __stop_engine_search(self):
        """Stop the current engine search operation.
        
        Sends a stop command to the engine to halt its current analysis.
        Used for manual search interruption.
        """

        self.__engine_exec.protocol.stop()

    def start_game(self, recursive=True):
        """Start and manage a complete game session.
        
        Main game loop that handles move detection, engine communication,
        and automated gameplay. Manages timing, move validation, and game state.
        
        Args:
            recursive (bool, optional): Whether to continue playing after the
                                      first move. Defaults to True.
        
        The method contains nested helper functions:
        - click(): Handles automated or manual move execution
        - calc_time_left(): Calculates remaining time for moves
        - recursive_get_info(): Retrieves engine move recommendations
        - recursive_play(): Main game loop for continuous play
        
        Side Effects:
            - Updates game state and UI
            - Sends commands to engine
            - Executes mouse clicks on detected moves
            - Manages game timing and move history
        
        Raises:
            AssertionError: If engine is not ready within timeout period.
        """

        def click(*coord):
            # Check auto mode
            if self.mode.get():
                self.__board.click(*coord)
            else:
                self.text_box.set('Wait key: ALT + M to continue!')
                keyboard.wait('alt+m')
                self.__board.click(*coord)

        def calc_time_left(begin_at, during):
            return (begin_at - during + self.time_plus.get()) * 1000
        
        def recursive_get_info(time_left) -> Move | None:
            """
            Recursive get search info.

            Args:
                time_left (int): Initialize time_left

            Return:
                Move: Move object.
                None: None for no information.
            """
            while self.__state:
                try:                    
                    # Represent to View
                    best_move = self.__engine_exec._receive('coord', timeout=time_left)
                    if best_move:
                        best_move = Move(best_move)
                        self.__display_search_info(reset=True)   

                        self.text_box.set('[BestMove]', best_move.to_alphabet())
                        return best_move
                except:
                    continue
            return None
            
        def recursive_play(begin_time: int, move_stack: MoveStack):
            """
            Recursive playing until terminated.

            Args:
                begin_time (int): Initialize start time
                move_stack (int): Initialize move stack to mangage moves.
            """
            while self.__state:                
                # Step 1: Set time_left
                time_start = time.perf_counter()
                self.__engine_exec.protocol.configure({'time_left': begin_time})

                # Step 2: Get move || Manage by turn
                if (move := detect_move(*self.__board_position, self.__distance)) is not None and \
                    move not in move_stack:
                    # Step 3: Send to engine                        
                    move     = Move(move)
                    move_stack.put(move)
                    
                    self.text_box.clear()
                    self.text_box.set(f'--> Time Left: {convert_time(begin_time)}')

                    self.__engine_exec.protocol.send_command('turn', move.to_strnum())

                    # Step 4: Display & click
                    output   = recursive_get_info(begin_time / 1000)

                    move_stack.put(output)
                    if output is not None:
                        click(*self.__board.move_to_coord(*output.to_num()))

                    # Step 5: Update time_left

                    time_end   = time.perf_counter()
                    begin_time = calc_time_left(begin_time / 1000, time_end - time_start)

                    # Step 6: Check win
                    if move_stack.is_win():
                        self.stop_game()
        

        try:            
            self.__state = True
            move_stack        = MoveStack()
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
            for move in opening: 
                move_stack.put(Move(move))

            # STEP 2: Send to Engine
            moves_str  = "\n".join([f"{move[0]},{move[1]},{1 if len(opening) % 2 == idx % 2 else 2}" 
                                    for idx, move in enumerate(opening)])
            self.__engine_exec.protocol.send_command(f'board\n{moves_str}\ndone')

            # Step 3: Represent
            output     = recursive_get_info(self.time_match.get())
            move_stack.put(output)
            if output is not None:
                click(*self.__board.move_to_coord(*output.to_num()))

            # Step 4: Local update time
            time_end   = time.perf_counter()
            time_left  = calc_time_left(self.time_match.get(), time_end - time_start)
            if recursive:
                recursive_play(time_left, move_stack)
        finally:
            self.__state = False
