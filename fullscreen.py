"""通过 Alt+Enter 切换 Forza Horizon 3/4/5 的全屏模式。

UWP/Win32 版 Forza 用 Alt+Enter 切换全屏，这是键盘驱动的开关，没有直接
的 Win32 API。本模块仅在 Forza 窗口处于前台时发送按键组合，避免影响其他应用。
"""

import ctypes
import time
from ctypes import windll

import win32con
import win32gui

from windows import active_window, game_version

VK_MENU = 0x12    # Left Alt
VK_RETURN = 0x0D  # Enter
KEYEVENTF_KEYUP = win32con.KEYEVENTF_KEYUP


def _send_alt_enter(hwnd):
    """向 Forza 窗口发送 Alt+Enter 以切换全屏。

    先强制窗口置前，再把四个按键事件拉开间隔发送，确保游戏可靠识别组合键
    （一次性瞬时 SendInput 常被游戏忽略）。
    """
    user32 = windll.user32

    if hwnd:
        try:
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            win32gui.SetForegroundWindow(hwnd)
        except Exception:
            pass
        time.sleep(0.05)

    # 依次按下 Alt、Enter，再依次释放 Enter、Alt，键间留微小间隔
    user32.keybd_event(VK_MENU, 0, 0, 0)
    time.sleep(0.01)
    user32.keybd_event(VK_RETURN, 0, 0, 0)
    time.sleep(0.01)
    user32.keybd_event(VK_RETURN, 0, KEYEVENTF_KEYUP, 0)
    time.sleep(0.01)
    user32.keybd_event(VK_MENU, 0, KEYEVENTF_KEYUP, 0)


def is_forza_focused():
    """返回 (focused, title, hwnd)；focused 为 True 表示前台窗口是 Forza Horizon 3/4/5。"""
    title, hwnd = active_window()
    return bool(game_version(title)), title, hwnd


def toggle_forza_fullscreen(verbose=True):
    """切换前台 Forza 窗口的全屏状态；Forza 未聚焦时返回 False。"""
    focused, title, hwnd = is_forza_focused()
    if not focused:
        if verbose:
            print(f"Forza Horizon 3/4/5 not focused (current: {title!r}); skip.")
        return False

    if verbose:
        print(f"Toggling fullscreen for {title!r} (hwnd={hwnd})")
    _send_alt_enter(hwnd)
    return True


if __name__ == "__main__":
    # 演示：按 Scroll Lock 切换 Forza 全屏（仅在前台窗口为 Forza 时生效）
    from pynput import keyboard

    print("Press Scroll Lock to toggle Forza fullscreen (only when focused).")
    print("Ctrl+C to exit.")
    with keyboard.Listener(
        on_press=lambda key: key == keyboard.Key.scroll_lock and toggle_forza_fullscreen()
    ) as listener:
        listener.join()