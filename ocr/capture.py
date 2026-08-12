"""屏幕区域截图（mss）。"""

import cv2
import numpy as np
import mss


def capture_region(region):
    """截取屏幕区域 (left, top, width, height)，返回 BGR 图像。"""
    left, top, width, height = region
    monitor = {"left": left, "top": top, "width": width, "height": height}
    with mss.mss() as sct:
        shot = sct.grab(monitor)
    image = np.array(shot)
    return cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)