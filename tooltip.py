"""调校比值悬浮窗（无边框、置顶的 Tkinter 窗口）。"""

import math
import tkinter as tk
from queue import Empty, Queue

from config import FONT_NAME, FONT_SIZE, HIGHLIGHT_COLOR, TOOLTIP_ANCHORS, TOOLTIP_LABEL_POS
from ocr.parser import parse_ratio
from windows import game_viewport


class Tooltip:
    """在游戏画面内显示 调校比值（旧 ÷ 新） 的悬浮窗。

    Tkinter 必须在主线程运行，因此所有界面更新通过队列投递到
    mainloop 调度线程执行。
    """

    def __init__(self, title="RatioTooltip", font_size=16):
        self.font_size = font_size
        self.root = tk.Tk()
        self.root.title(title)
        self.root.overrideredirect(True)
        self.root.wm_resizable(False, False)
        self.root.wm_attributes("-topmost", True)
        self.root.wm_attributes("-toolwindow", True)
        self.root.wm_attributes("-disabled", True)
        self.root.wm_attributes("-transparentcolor", "blue")
        self.root.configure(background="blue")

        self.queue = Queue()
        self.max_new_ratio = 0.0  # 当前会话右侧结果的最大值
        self._right_is_max = False

        self.label_left = tk.Label(
            self.root,
            text="",
            font=(FONT_NAME, 9, "bold"),
            bg="blue",
            fg="#fff",
        )
        self.label_right = tk.Label(
            self.root,
            text="",
            font=(FONT_NAME, 9, "bold"),
            bg="blue",
            fg="#fff",
        )
        self.root.bind("<Button-1>", lambda e: self.close())
        self._poll_queue()

    def _poll_queue(self):
        """定时执行队列中的界面更新任务。"""
        try:
            while True:
                action = self.queue.get_nowait()
                action()
        except Empty:
            pass
        self.root.after(50, self._poll_queue)

    def _schedule(self, func):
        """把界面操作投递到主线程队列（非主线程调用时安全）。"""
        try:
            self.queue.put(func)
        except Exception:
            pass

    def _adaptive_font_size(self, width, height):
        """根据窗口面积相对 1920x1080 基准调整字号，范围 [6, FONT_SIZE*3]。"""
        area = width * height
        size = round(FONT_SIZE * math.sqrt(area / (1920 * 1080)))
        return max(6, min(FONT_SIZE * 3, size))

    def update(self, width, font_size, x, y, text_left, text_right, left_relx, right_relx):
        def _update():
            # 窗口高度由字号推导，确保文字始终完整显示且不改变定位锚点
            height = max(font_size * 2 + 13, 20)
            self.root.geometry(f"{width}x{height}+{x}+{y}")
            self.label_left.config(
                text=text_left,
                font=(FONT_NAME, font_size, "bold"),
            )
            self.label_right.config(
                text=text_right,
                font=(FONT_NAME, font_size, "bold"),
                fg=HIGHLIGHT_COLOR if self._right_is_max else "#fff",
            )
            self.label_left.place(relx=left_relx, rely=0.5, anchor="center")
            self.label_right.place(relx=1 - right_relx, rely=0.5, anchor="center")

        self._schedule(_update)

    def reset_max(self):
        """OCR 开启时调用，重置当前会话的右侧结果最大值。"""
        self.max_new_ratio = 0.0

    def display_ratio(self, ocr_text, region, window_rect, version):
        """解析 OCR 文本并更新悬浮窗；解析失败时静默返回。"""
        parsed = parse_ratio(ocr_text, version)
        if parsed is None:
            return

        # 记录右侧结果并更新会话最大值；值为会话最大值时高亮
        self._right_is_max = parsed.new_ratio != "0" and parsed.new_value >= self.max_new_ratio
        if parsed.new_value > self.max_new_ratio:
            self.max_new_ratio = parsed.new_value

        print(
            f"{parsed.a} ÷ {parsed.b} = {parsed.old_ratio} "
            f"---- {parsed.c} ÷ {parsed.d} = {parsed.new_ratio}"
        )

        width = region[2]

        # 在 16:9 游戏画面内按固定锚点定位，而不是跟随 OCR 区域 / 窗口
        win_width = window_rect[2] - window_rect[0]
        win_height = window_rect[3] - window_rect[1]
        gx, gy, gw, gh = game_viewport(win_width, win_height)
        anchor = TOOLTIP_ANCHORS.get(version, TOOLTIP_ANCHORS["3"])
        x = window_rect[0] + gx + int(gw * anchor["x"]) - width // 2
        y = window_rect[1] + gy + int(gh * anchor["y"])

        # 字号按游戏窗口画面区域的实际宽高动态调整
        font_size = self._adaptive_font_size(win_width, win_height)
        left_relx, right_relx = TOOLTIP_LABEL_POS.get(version, TOOLTIP_LABEL_POS["3"])

        self.update(width, font_size, x, y, parsed.old_ratio, parsed.new_ratio, left_relx, right_relx)
        self.show()

    def show(self):
        def _show():
            self.root.wm_attributes("-alpha", 1)

        self._schedule(_show)

    def hide(self):
        def _hide():
            self.root.wm_attributes("-alpha", 0)

        self._schedule(_hide)

    def start(self):
        self.root.mainloop()

    def close(self):
        self.root.destroy()