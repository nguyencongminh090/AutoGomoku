from utils import *
from tkinter import Tk
import time
import cv2


def screen_capture():
    """
    Capture a screenshot of the screen and display it in a Tkinter window.
    """
    window         = Tk()
    screen_capture = ScreenCapture(window)    
    game_object.board_position = screen_capture.get()
    window.withdraw()
    return


def show_info():
    if game_object.board_position is not None:
        detected_board                    = detect_board(game_object.board_position[0], 
                                                         top=game_object.board_position[2], 
                                                         left=game_object.board_position[1])
        game_object.board_actual_position = detected_board
        game_object.board                 = Board((detected_board[0], detected_board[1]), (detected_board[2], detected_board[3]), 15, 15)
        print('Found:', detected_board)


def get_coordinate():    
    if game_object.board_actual_position is not None:
        coordinates = detect_opening(game_object.board_actual_position[0], 
                                     game_object.board_actual_position[1],
                                     game_object.board_actual_position[3],
                                     game_object.board_actual_position[2], 
                                     game_object.board_actual_position[3] / 14)
        game_object.coordinates = coordinates
        print('Coordinates:', coordinates)

def test_click():
    if game_object.board is not None and game_object.coordinates is not None:
        print('Clicking on coordinates...')
        for coord in game_object.coordinates:
            game_object.board.click(*game_object.board.move_to_coord(coord[0], coord[1]))
            time.sleep(0.05)

def stop(listener_instance: Listener):
    """
    Stop the listener instance and close the Tkinter window.
    """
    listener_instance.signal_stop()
    return


class Object:
    """
    A simple object class to hold a value.
    """
    def __init__(self):
        self.board_position        = None
        self.board_actual_position = None
        self.coordinates           = None
        self.board                 = None


listener    = Listener()
game_object = Object()

with Listener(max_callback_workers=1, debounce_ms=500) as listener:
    try:
        listener.add_hotkey('ctrl+d', screen_capture)
        listener.add_hotkey('esc', lambda: stop(listener))
        listener.add_hotkey('ctrl+i', show_info)
        listener.add_hotkey('ctrl+g', get_coordinate)
        listener.add_hotkey('ctrl+c', test_click)
        while not listener._stop_event.is_set():
            time.sleep(0.1)
    except HotkeyError:
        pass
    except Exception as e:
        raise
    finally:
        print('Application shutting down')
