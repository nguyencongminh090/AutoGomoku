import os
from typing import List, Tuple

import mss
import cv2
import mss.base
import numpy as np
from PIL     import Image

from .helper import CustomArr, ArrangedArr


class ScreenServices:
    def screenshot(self) -> cv2.typing.MatLike:
        """
        Capture a screenshot of the entire primary monitor.

        Returns:
            cv2.typing.MatLike: The captured screenshot as an RGB image.
        """
        with mss.mss() as sct:
            image = cv2.cvtColor(np.array(sct.grab(sct.monitors[0])), cv2.COLOR_BGR2RGB)
        return image


    def screenshot_region(self,
                        x1 : int,
                        y1 : int,
                        h  : int,
                        w  : int):
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
        image = self.screenshot()
        image = image[y1:y1 + h, x1:x1 + w]
        return image


    def display(self, region: List[int], title='AutoGomoku'):
        cv2.imshow(title, cv2.cvtColor(self.screenshot_region(*region), cv2.COLOR_BGR2RGB))
        cv2.waitKey(5000)
        cv2.destroyAllWindows()
