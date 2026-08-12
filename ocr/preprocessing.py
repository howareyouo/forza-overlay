"""按游戏版本对截图做二值化预处理，提取可读文本。"""

import cv2

from config import OCR_UPSCALE_FACTOR

BLUE_THRESHOLD = 199
CHANNEL_OR_THRESHOLD = 200


def _threshold_channel(image, channel, value):
    return cv2.threshold(image[:, :, channel], value, 255, cv2.THRESH_BINARY)[1]


def process_horizon3(image: cv2.typing.MatLike):
    g_channel = _threshold_channel(image, 1, CHANNEL_OR_THRESHOLD)
    r_channel = _threshold_channel(image, 2, CHANNEL_OR_THRESHOLD)
    return cv2.bitwise_or(g_channel, r_channel)


def process_horizon4(image: cv2.typing.MatLike):
    return _threshold_channel(image, 0, BLUE_THRESHOLD)


PREPROCESSORS = {
    "3": process_horizon3,
    "4": process_horizon4,
    "44": process_horizon4,
    "5": process_horizon4,
}


def preprocess_for_ocr(image, version):
    """版本化预处理 + 放大，返回可直接送入 OCR 引擎的图像；未知版本返回 None。"""
    preprocess = PREPROCESSORS.get(version)
    if preprocess is None:
        return None

    processed = preprocess(image)
    h, w = processed.shape[:2]
    return cv2.resize(
        processed,
        (w * OCR_UPSCALE_FACTOR, h * OCR_UPSCALE_FACTOR),
        interpolation=cv2.INTER_CUBIC,
    )