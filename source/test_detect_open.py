from utils import detect_opening
from utils import screenshot_region
from utils import Listener
import time
import cv2


left, top, width, height = (530, 160, 519, 519)
distance                 = width / 14


def show_image():
    cv2.imshow('Image', screenshot_region(left, top, height, width))
    cv2.waitKey(0)


def show_coordinates():
    coordinates = detect_opening(left, top, width, height, distance)
    for coord in coordinates:
        print(f"Coordinate: {coord}")


with Listener(max_callback_workers=1, debounce_ms=500) as listener:
    listener.add_hotkey('ctrl+d', show_image)
    listener.add_hotkey('ctrl+i', show_coordinates)
    listener.add_hotkey('esc', lambda: listener.signal_stop())
    while not listener._stop_event.is_set():
        time.sleep(0.1)