"""Win32 窗口工具：活动窗口、游戏版本识别、窗口与画面坐标、OCR 采样区域计算。"""

import win32gui
import ctypes
import re
from ctypes import windll, wintypes
from config import OCR_REGION_RATIO

SCREEN_WIDTH = windll.user32.GetSystemMetrics(0)
SCREEN_HEIGHT = windll.user32.GetSystemMetrics(1)
# 游戏输出固定为 16:9，用于把窗口客户区换算成画面区域（去黑边）
GAME_ASPECT = 16 / 9

_VERSION_PATTERN = re.compile(r"(?:Forza Horizon|地平线)\s*([345])")


def active_window():
    """返回当前前台窗口的 (标题, hwnd)，无窗口时返回 (None, None)。"""
    hwnd = windll.user32.GetForegroundWindow()
    if hwnd:
        length = windll.user32.GetWindowTextLengthW(hwnd)
        if length > 0:
            buffer = ctypes.create_unicode_buffer(length + 1)
            windll.user32.GetWindowTextW(hwnd, buffer, length + 1)
            return buffer.value, hwnd
    return None, None


def game_version(title):
    """识别 Forza Horizon 版本号（3/4/5），兼容英文与中文标题；失败返回 None。

    英文：Forza Horizon 3 / 4 / 5
    中文：极限竞速：地平线3 / 4 / 5（冒号可能为半角或全角）
    """
    if not title:
        return None
    match = _VERSION_PATTERN.search(title)
    return match.group(1) if match else None


class _WINDOWINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("rcWindow", wintypes.RECT),
        ("rcClient", wintypes.RECT),
        ("dwStyle", wintypes.DWORD),
        ("dwExStyle", wintypes.DWORD),
        ("dwWindowStatus", wintypes.DWORD),
        ("cxWindowBorders", wintypes.UINT),
        ("cyWindowBorders", wintypes.UINT),
        ("atomWindowType", wintypes.ATOM),
        ("wCreatorVersion", wintypes.WORD),
    ]


def is_fullscreen(hwnd):
    """判断窗口是否铺满整个屏幕（用于区分全屏/窗口化渲染路径）。"""
    rect = wintypes.RECT()
    windll.user32.GetWindowRect(hwnd, ctypes.byref(rect))
    return (rect.right - rect.left == SCREEN_WIDTH
            and rect.bottom - rect.top == SCREEN_HEIGHT)


def window_client_rect(hwnd, window_title):
    """返回游戏画面（不含标题栏）在屏幕上的真实坐标 (left, top, right, bottom)。"""
    rect = wintypes.RECT()
    windll.user32.GetWindowRect(hwnd, ctypes.byref(rect))

    wi = _WINDOWINFO()
    wi.cbSize = ctypes.sizeof(_WINDOWINFO)
    if windll.user32.GetWindowInfo(hwnd, ctypes.byref(wi)):
        left, top, right, bottom = wi.rcClient.left, wi.rcClient.top, wi.rcClient.right, wi.rcClient.bottom
        if right > left and bottom > top:
            # 无边框窗口化时 GetWindowInfo 会忽略 DWM 标题栏，直接用 48px 默认标题栏高度扣除
            top += 48
            return (left, top, right, bottom)
        # 客户区尺寸异常（如最小化），退回窗口本身
        return (rect.left, rect.top, rect.right, rect.bottom)

    # GetWindowInfo 失败：退回按标题栏估算
    titlebar = 42 if window_title == "Forza Horizon 5" else 48
    return (rect.left, rect.top + titlebar, rect.right, rect.bottom)


def game_viewport(win_width, win_height):
    """在客户区 (win_width x win_height) 内计算 16:9 游戏画面的区域 (x, y, w, h)。

    游戏输出固定为 16:9：窗口更宽时左右留黑边，更高时上下留黑边。
    """
    if win_width / win_height >= GAME_ASPECT:
        game_height = win_height
        game_width = int(game_height * GAME_ASPECT)
        return (win_width - game_width) // 2, 0, game_width, game_height
    game_width = win_width
    game_height = int(game_width / GAME_ASPECT)
    return 0, (win_height - game_height) // 2, game_width, game_height


# 允许在窗口化模式下采样的版本（其余版本要求全屏）
WINDOWED_ALLOWED_VERSIONS = {"5"}


def compute_ocr_region():
    """返回 (region, window_rect, version)；不在受支持的 Forza 窗口时返回 None。

    - region:       OCR 采样区域 (left, top, width, height)
    - window_rect:  游戏窗口画面坐标 (left, top, right, bottom)
    - version:      游戏版本号（"3"/"4"/"5"）
    """
    title, hwnd = active_window()
    version = game_version(title)
    if not version:
        print("Not in Forza Horizon")
        return None

    window_rect = window_client_rect(hwnd, title)
    if is_fullscreen(hwnd) and version not in WINDOWED_ALLOWED_VERSIONS:
        print("Not in fullscreen mode")
        return None

    win_width = window_rect[2] - window_rect[0]
    win_height = window_rect[3] - window_rect[1]
    ratio = OCR_REGION_RATIO[version]

    # 先由窗口尺寸换算出 16:9 游戏画面区域（去黑边），再套用相对比例
    gx, gy, gw, gh = game_viewport(win_width, win_height)
    left = window_rect[0] + gx + int(gw * ratio["left"])
    top = window_rect[1] + gy + int(gh * ratio["top"])
    right = window_rect[0] + gx + int(gw * ratio["right"])
    bottom = window_rect[1] + gy + int(gh * ratio["bottom"])

    return (left, top, right - left, bottom - top), window_rect, version