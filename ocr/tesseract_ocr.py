"""OCR 引擎：屏幕/文件截图 → 预处理 → 文本识别。"""

import os

import cv2
import pytesseract

from ocr.capture import capture_region
from ocr.preprocessing import preprocess_for_ocr
from utils import show_image

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def available():
    """后端是否可用（pytesseract 为模块级硬依赖，能导入即视为可用）。"""
    return True


def ocr_from_screen(region, version):
    """截取屏幕区域并识别文本；未知版本返回空字符串。"""
    image = capture_region(region)
    return _recognize(image, version)


def ocr_from_file(image_path, version="4"):
    """离线调试：从图片文件识别文本（相对路径以项目根目录为基准）。"""
    if not os.path.isabs(image_path):
        image_path = os.path.join(PROJECT_ROOT, image_path)
    image = cv2.imread(image_path)
    return _recognize(image, version)


def _recognize(image, version):
    """对图像做版本化预处理、放大后识别，返回识别文本。"""
    processed = preprocess_for_ocr(image, version)
    if processed is None:
        print(f"Unsupported game version: {version}")
        return ""

    show_image(processed)
    return pytesseract.image_to_string(processed)


if __name__ == "__main__":
    # 调试：识别项目根目录下的离线截图
    result = ocr_from_file("screenshot4.png", version="4")
    print(result)