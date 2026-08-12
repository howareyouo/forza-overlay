"""通用工具：按键归一化与图像保存/查看（调试用）。"""

import os

import cv2
from pynput import keyboard


def normalize_key(key) -> str:
    """归一化按键对象。

    - 功能键（如 ctrl_r）→ 按键名 "ctrl_r"
    - 可打印字符键 → 字符本身（如 "q"）
    - 无字符的原始虚键 → 显式 "<vk>" 形式（如 "<207>"）
    """
    if isinstance(key, keyboard.Key):
        return key.name
    if isinstance(key, keyboard.KeyCode):
        if key.char is not None:
            return key.char
        return f"<{key.vk}>"
    return str(key)


def show_image(image: cv2.typing.MatLike, filename: str = "screenshot.png") -> str:
    """将图像保存到桌面并返回文件路径（调试时查看截图用）。"""
    desktop_dir = os.path.join(os.path.expanduser("~"), "Desktop")
    os.makedirs(desktop_dir, exist_ok=True)
    filepath = os.path.join(desktop_dir, filename)
    cv2.imwrite(filepath, image)
    print(f"Saved to {filepath}")
    return filepath