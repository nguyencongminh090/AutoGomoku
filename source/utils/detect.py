import cv2
import numpy as np
from typing import Tuple, Optional
from utils  import group_overlapping_contours


def detect_board(
    img          : np.ndarray,
    top          : int  = 0,
    left         : int  = 0,
    rectangle    : bool = False
) -> Tuple[Optional[int], Optional[int], Optional[int], Optional[int]]:
    """
    Detect a game board in an image, returning its top-left corner and size.

    Processes the image to find the largest near-square or rectangular region,
    optionally masking circular objects (e.g., game pieces).

    Args:
        img: Input RGB image as a numpy array.
        top: Y-offset to adjust output coordinates.
        left: X-offset to adjust output coordinates.
        enable_border: If True, detect and mask circular objects.
        rectangle: If True, allow any rectangle; if False, require near-square (0.9 <= w/h <= 1.1).

    Returns:
        Tuple of (x, y, w, h) for the board's top-left corner and size, or (None, None, None, None)
        if no board is found.

    Raises:
        ValueError: If img is invalid (empty or not RGB).
    """
    if not isinstance(img, np.ndarray) or img.size == 0 or img.shape[2] != 3:
        raise ValueError("Input image must be a non-empty RGB numpy array")

    # Convert to grayscale and apply adaptive thresholding
    gray          = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh     = cv2.threshold(gray, 120, 255, cv2.THRESH_BINARY)
    thresh_inv    = cv2.bitwise_not(thresh)  # Invert for white background

    # Morphological closing to remove noise
    kernel        = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    morph         = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

    # Refine threshold (optional: adjust based on intent)
    thresh        = cv2.bitwise_and(thresh_inv, thresh_inv, mask=morph)

    # Find and group contours
    contours, _   = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contour_group = group_overlapping_contours(contours)

    # Select largest near-square or rectangular region
    min_area      = 1000  # Minimum board area
    cur_info      = (None, None, None, None)

    for contour in contour_group:
        area         = cv2.contourArea(contour)
        if area < min_area:
            continue
        rect         = cv2.minAreaRect(contour)
        box          = cv2.boxPoints(rect)
        box          = np.int0(box)
        x1           = int(min(box[:, 0]))
        y1           = int(min(box[:, 1]))
        w            = int(max(box[:, 0]) - x1)
        h            = int(max(box[:, 1]) - y1)
        aspect_ratio = float(w) / h if h > 0 else 1.0

        if (rectangle or 0.9 <= aspect_ratio <= 1.1):
            min_area = max(min_area, area)
            cur_info = (x1 + left, y1 + top, w, h)

    return cur_info