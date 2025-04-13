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
    window.destroy()
    return


def show_info():
    if game_object.board_position is not None:
        detected_board = detect_board(game_object.board_position[0], top=game_object.board_position[2], left=game_object.board_position[1])
        board_image = img_crop(screenshot(), detected_board[0], detected_board[1], detected_board[3], detected_board[2])
        cv2.imshow('Detected Board', board_image)
        cv2.waitKey()


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
        self.board_position = None


listener    = Listener()
game_object = Object()

with Listener(max_callback_workers=1, debounce_ms=500) as listener:
    try:
        listener.add_hotkey('ctrl+d', screen_capture)
        listener.add_hotkey('esc', lambda: stop(listener))
        listener.add_hotkey('ctrl+i', show_info)
        while not listener._stop_event.is_set():
            time.sleep(0.1)
    except HotkeyError:
        pass
    except Exception as e:
        raise
    finally:
        print('Application shutting down')
