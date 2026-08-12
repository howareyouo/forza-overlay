"""XInput 手柄轮询模块：独立于游戏进程读取手柄按键。

原理：xinput.dll 是共享轮询总线，任何进程都能在任何时候读取手柄状态，
不依赖游戏进程（商店版 UWP 或 Steam 版 Win32 均可）。

按键以与 UWP VK_GAMEPAD_* 一致的虚键名（如 "<195>"）回调，
这样 main.py 的既有 config 触发逻辑可以原样复用。

注意：XInput 只能读到 X-input 兼容设备（即 Xbox 模式）。杂牌手柄需
切换到 Xbox/X-input 模式，或通过 x360ce 等工具转换。
"""

import ctypes
import threading
import time
from ctypes import wintypes
from typing import Callable, Optional

# ---- XInput 常量 ----
ERROR_DEVICE_NOT_CONNECTED = 1167

# XINPUT_GAMEPAD.wButtons 按键位
GAMEPAD_DPAD_UP = 0x0001
GAMEPAD_DPAD_DOWN = 0x0002
GAMEPAD_DPAD_LEFT = 0x0004
GAMEPAD_DPAD_RIGHT = 0x0008
GAMEPAD_START = 0x0010
GAMEPAD_BACK = 0x0020
GAMEPAD_LEFT_THUMB = 0x0040
GAMEPAD_RIGHT_THUMB = 0x0080
GAMEPAD_LEFT_SHOULDER = 0x0100
GAMEPAD_RIGHT_SHOULDER = 0x0200
GAMEPAD_A = 0x1000
GAMEPAD_B = 0x2000
GAMEPAD_X = 0x4000
GAMEPAD_Y = 0x8000

# XInput 按键位 → 归一化键名（与 config.py 中 UWP VK_GAMEPAD 虚键码一致）
BUTTON_TO_KEY = {
    GAMEPAD_DPAD_UP: "<203>",
    GAMEPAD_DPAD_DOWN: "<204>",
    GAMEPAD_DPAD_LEFT: "<205>",
    GAMEPAD_DPAD_RIGHT: "<206>",
    GAMEPAD_START: "<207>",
    GAMEPAD_BACK: "<208>",
    GAMEPAD_LEFT_THUMB: "<209>",
    GAMEPAD_RIGHT_THUMB: "<210>",
    GAMEPAD_LEFT_SHOULDER: "<200>",
    GAMEPAD_RIGHT_SHOULDER: "<199>",
    GAMEPAD_A: "<195>",
    GAMEPAD_B: "<196>",
    GAMEPAD_X: "<197>",
    GAMEPAD_Y: "<198>",
}

# 扳机视为按键的触发阈值（0~255）
TRIGGER_THRESHOLD = 30


class XINPUT_GAMEPAD(ctypes.Structure):
    _fields_ = [
        ("wButtons", wintypes.WORD),
        ("bLeftTrigger", ctypes.c_ubyte),
        ("bRightTrigger", ctypes.c_ubyte),
        ("sThumbLX", ctypes.c_short),
        ("sThumbLY", ctypes.c_short),
        ("sThumbRX", ctypes.c_short),
        ("sThumbRY", ctypes.c_short),
    ]


class XINPUT_STATE(ctypes.Structure):
    _fields_ = [
        ("dwPacketNumber", wintypes.DWORD),
        ("Gamepad", XINPUT_GAMEPAD),
    ]


def _load_xinput() -> ctypes.WinDLL:
    """按优先级加载 xinput 动态库。"""
    for name in ("xinput1_4.dll", "xinput1_3.dll", "xinput9_1_0.dll"):
        try:
            dll = ctypes.WinDLL(name)
            dll.XInputGetState.argtypes = [
                wintypes.DWORD,
                ctypes.POINTER(XINPUT_STATE),
            ]
            dll.XInputGetState.restype = wintypes.DWORD
            return dll
        except OSError:
            continue
    raise OSError("未找到 xinput 动态库，手柄支持未启用")


class GamepadMonitor(threading.Thread):
    """轮询 XInput 手柄，把按键事件回调给 on_press / on_release。

    回调签名与 pynput 键盘监听一致：回调收到归一化键名（str），
    例如按下 A 键会先后回调 on_press("<195>")、on_release("<195>")。
    """

    def __init__(
        self,
        on_press: Callable[[str], None],
        on_release: Callable[[str], None],
        interval: float = 0.016,
    ):
        super().__init__(daemon=True, name="gamepad-monitor")
        self.on_press = on_press
        self.on_release = on_release
        self.interval = interval
        self._stop = threading.Event()
        self._xinput: Optional[ctypes.WinDLL] = None
        # player index -> (prev_buttons, prev_lt_pressed, prev_rt_pressed)
        self._stated: dict[int, tuple[int, bool, bool]] = {}

    def stop(self) -> None:
        self._stop.set()

    def run(self) -> None:
        try:
            self._xinput = _load_xinput()
        except OSError as e:
            print(f"[gamepad] {e}")
            return
        connected = set()
        while not self._stop.is_set():
            now = set(self._tick())
            if now != connected:
                for idx in sorted(now - connected):
                    print(f"[gamepad] 已连接手柄（槽位 {idx}）")
                for idx in sorted(connected - now):
                    print(f"[gamepad] 手柄已断开（槽位 {idx}）")
                connected = now
            self._stop.wait(self.interval)

    def _tick(self):
        """轮询所有槽位，返回当前连接的槽位集合。"""
        connected = set()
        for player in range(4):
            state = XINPUT_STATE()
            res = self._xinput.XInputGetState(player, ctypes.byref(state))
            if res == ERROR_DEVICE_NOT_CONNECTED:
                self._stated.pop(player, None)
                continue
            if res != 0:
                continue
            connected.add(player)
            self._pump(player, state.Gamepad)
        return connected

    def _pump(self, player: int, pad: XINPUT_GAMEPAD) -> None:
        buttons = pad.wButtons
        lt = pad.bLeftTrigger > TRIGGER_THRESHOLD
        rt = pad.bRightTrigger > TRIGGER_THRESHOLD
        prev_buttons, prev_lt, prev_rt = self._stated.get(player, (0, False, False))

        changed = prev_buttons ^ buttons
        for bit, key in BUTTON_TO_KEY.items():
            if not (changed & bit):
                continue
            (self.on_press if buttons & bit else self.on_release)(key)

        if lt != prev_lt:
            (self.on_press if lt else self.on_release)("<201>")
        if rt != prev_rt:
            (self.on_press if rt else self.on_release)("<202>")

        self._stated[player] = (buttons, lt, rt)


if __name__ == "__main__":
    # 冒烟测试：打印手柄按键事件
    def _press(key):
        print(f"press   {key}")

    def _release(key):
        print(f"release {key}")

    monitor = GamepadMonitor(_press, _release, interval=0.05)
    monitor.start()
    try:
        while monitor.is_alive():
            time.sleep(0.5)
    except KeyboardInterrupt:
        monitor.stop()