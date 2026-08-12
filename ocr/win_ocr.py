"""Windows 11 内置 OCR（Windows.Media.Ocr）实现。

对截图先做与 tesseract_ocr.py 相同的版本化预处理（见 ocr/preprocessing.py），
再交由系统自带的 OCR 引擎识别，无需安装 Tesseract。

依赖（已写入 requirements.txt）：
    winrt-Windows.Media.Ocr
    winrt-Windows.Graphics.Imaging
    winrt-Windows.Storage.Streams
"""

import asyncio
import os

import cv2

from ocr.capture import capture_region
from ocr.preprocessing import preprocess_for_ocr
from utils import show_image

try:
    import winrt.windows.graphics.imaging as _imaging
    import winrt.windows.media.ocr as _ocr
    import winrt.windows.storage.streams as _streams

    BACKEND_AVAILABLE = True
except ImportError:
    BACKEND_AVAILABLE = False

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def available():
    """WinRT OCR 后端是否可用（依赖已安装且系统为 Win10 1803+）。"""
    return BACKEND_AVAILABLE


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
    """对图像做版本化预处理、放大后调用 Windows 内置 OCR，返回识别文本。"""
    if not available():
        print(
            "Windows OCR backend unavailable: install winrt-Windows.Media.Ocr, "
            "winrt-Windows.Graphics.Imaging and winrt-Windows.Storage.Streams"
        )
        return ""

    processed = preprocess_for_ocr(image, version)
    if processed is None:
        print(f"Unsupported game version: {version}")
        return ""

    show_image(processed)
    try:
        return _run(_recognize_async(processed))
    except Exception as exc:
        print(f"Windows OCR failed: {exc}")
        return ""


async def _recognize_async(processed):
    """将预处理后的 ndarray 编码为 PNG 内存流，解码为 SoftwareBitmap 后调用系统 OCR。"""
    ok, encoded = cv2.imencode(".png", processed)
    if not ok:
        return ""

    stream = _streams.InMemoryRandomAccessStream()
    writer = _streams.DataWriter(stream)
    writer.write_bytes(encoded.tobytes())
    await writer.store_async()
    stream.seek(0)

    decoder = await _imaging.BitmapDecoder.create_async(stream)
    bitmap = await decoder.get_software_bitmap_async()

    engine = _ocr.OcrEngine.try_create_from_user_profile_languages()
    if engine is None:  # 用户配置文件语言无 OCR 支持时，退回第一个可用识别语言
        languages = _ocr.OcrEngine.available_recognizer_languages
        if not languages:
            return ""
        engine = _ocr.OcrEngine.try_create_from_language(languages[0])
    if engine is None:
        return ""

    result = await engine.recognize_async(bitmap)
    return result.text


def _run(coro):
    """在事件循环中执行协程；无外层循环时直接 asyncio.run。"""
    try:
        return asyncio.run(coro)
    except RuntimeError:  # 已在运行中的事件循环里被调用
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()


if __name__ == "__main__":
    import sys

    path = sys.argv[1] if len(sys.argv) > 1 else "screenshot4.png"
    print(repr(ocr_from_file(path, sys.argv[2] if len(sys.argv) > 2 else "4")))