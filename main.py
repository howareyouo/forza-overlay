"""Forza Horizon 调校比值悬浮工具：主逻辑与程序入口。

监听键盘：在游戏调校菜单翻页时截屏 OCR，并在悬浮窗显示新旧比值。
"""

import threading
from typing import Optional
from pynput import keyboard
from fullscreen import toggle_forza_fullscreen
from utils import normalize_key
from ocr.tesseract_ocr import ocr_from_screen
from windows import compute_ocr_region
from tooltip import Tooltip
from config import (
    FULLSCREEN_TOGGLE_KEY,
    KEEP_TOOLTIP_KEYS,
    OCR_DEBOUNCE_SECONDS,
    OCR_DISABLE_KEYS,
    OCR_TOGGLE_KEYS,
    OCR_TRIGGER_KEYS,
)

class ForzaOverlayApp:
    """监听键盘：在游戏调校菜单翻页时截屏 OCR，并在悬浮窗显示新旧比值。"""

    def __init__(self):
        self.tooltip: Optional[Tooltip] = None
        self.ocr_enabled = False
        self._ocr_timer: Optional[threading.Timer] = None

    def start_window(self) -> None:
        self.tooltip = Tooltip()
        self.tooltip.start()

    def on_press(self, key) -> None:
        key = normalize_key(key)
        if self.tooltip and key not in KEEP_TOOLTIP_KEYS:
            self.tooltip.hide()

    def on_release(self, key) -> None:
        key = normalize_key(key)
        
        if key in OCR_DISABLE_KEYS:
            if self.ocr_enabled:
                print("OCR is OFF")
                self.ocr_enabled = False
            return

        if key in OCR_TOGGLE_KEYS:
            if not self.ocr_enabled:
                print("OCR is ON")
                self.ocr_enabled = True
                if self.tooltip:
                    self.tooltip.reset_max()

        if self.ocr_enabled and key in OCR_TRIGGER_KEYS:
            self._schedule_ocr()

        if key == FULLSCREEN_TOGGLE_KEY:
            toggle_forza_fullscreen()

    def _schedule_ocr(self) -> None:
        """防抖调度：连续触发按键只执行一次 OCR。"""
        if self._ocr_timer is not None:
            self._ocr_timer.cancel()
        self._ocr_timer = threading.Timer(OCR_DEBOUNCE_SECONDS, self._run_ocr)
        self._ocr_timer.start()

    def _run_ocr(self) -> None:
        self.ocr_task()
        self._ocr_timer = None

    def ocr_task(self) -> None:
        region_info = compute_ocr_region()
        if region_info is None:
            return
        region, window_rect, version = region_info
        result = ocr_from_screen(region, version)
        if self.tooltip and result:
            self.tooltip.display_ratio(result, region, window_rect, version)

    def keyboard_listener(self) -> None:
        with keyboard.Listener(on_press=self.on_press, on_release=self.on_release) as listener:
            listener.join()

    def run(self) -> None:
        listener_thread = threading.Thread(target=self.keyboard_listener, daemon=True)
        listener_thread.start()

        print("------------------------------------")
        print("  Forza Horizon RatioTooltip Started")
        print("------------------------------------")

        self.start_window()


if __name__ == "__main__":
    ForzaOverlayApp().run()