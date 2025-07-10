import cv2
import numpy as np
import mss
from ttkbootstrap.scrolled import ScrolledText


class CustomArr:
    def __init__(self):
        self.__data = []

    def __setitem__(self, index, value):
        if index >= len(self.__data):
            self.__data.extend([None] * (index - len(self.__data) + 1))
        self.__data[index] = value

    def __len__(self):
        return len(self.__data)

    def __getitem__(self, index):
        return self.__data[index]
    
    def __iter__(self):
        return iter(self.__data)
    
    def __repr__(self):
        return repr(self.__data)
    

class ArrangedArr:
    def __init__(self):
        self.__data: CustomArr = CustomArr()
        self.__bIndex = 0
        self.__wIndex = 1

    def add(self, move, label):
        if label.lower() == 'b':
            self.__data[self.__bIndex] = move
            self.__bIndex += 2
        elif label.lower() == 'w':
            self.__data[self.__wIndex] = move
            self.__wIndex += 2

    def get(self):
            return self.__data


def img_crop(image, x1, y1, h, w):
    """
    Crop an image to the specified coordinates.

    Args:
        image: The image to crop.
        x1: The x-coordinate of the top-left corner.
        y1: The y-coordinate of the top-left corner.
        x2: The x-coordinate of the bottom-right corner.
        y2: The y-coordinate of the bottom-right corner.

    Returns:
        Cropped image.
    """
    return image[y1:y1+h, x1:x1+w]

def screenshot():
    """
    Capture a screenshot of the entire primary monitor.

    Returns:
        numpy.ndarray: The captured screenshot as an RGB image.
    """
    sct   = mss.mss()
    image = cv2.cvtColor(np.array(sct.grab(sct.monitors[0])), cv2.COLOR_BGR2RGB)
    return image


def screenshot_region(x1, y1, h, w):
    """
    Capture a screenshot of a specific region of the primary monitor.

    Args:
        x1 (int): The x-coordinate of the top-left corner of the region.
        y1 (int): The y-coordinate of the top-left corner of the region.
        h  (int): The height of the region.
        w  (int): The width of the region.

    Returns:
        numpy.ndarray: The captured screenshot of the specified region as an RGB image.
    """
    image = screenshot()
    image = image[y1:y1 + h, x1:x1 + w]
    return image


def convert_time(milliseconds: float) -> str:
    # Convert milliseconds -> minute:second(ms)
    seconds = int(milliseconds // 1000)
    ms      = int(milliseconds % 1000)
    minutes = seconds // 60
    secs    = seconds % 60
    return f"{minutes}:{secs:02d}({ms})"


class LogText:
    def __init__(self):        
        self.__log_text_box: ScrolledText = None

    def subscribe(self, text_box: ScrolledText):
        self.__log_text_box = text_box

    def set(self, *text):
        assert isinstance(self.__log_text_box, ScrolledText)
        self.__log_text_box.insert('end', ' '.join(text) + '\n')
        self.__log_text_box.see('end')

    def clear(self):
        assert isinstance(self.__log_text_box, ScrolledText)
        self.__log_text_box.delete('0.0', 'end')