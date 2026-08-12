"""集中管理所有可调配置常量。"""

# ---- 键盘按键 ----
# 开启 OCR 的按键
OCR_TOGGLE_KEYS = {"ctrl_r", "`", "<207>"}
# 关闭 OCR 的按键
OCR_DISABLE_KEYS = {"esc", "q", "e", "<201>", "<202>"}
# 触发一次识别的按键（开启状态下;含开启键,保持原行为）
OCR_TRIGGER_KEYS = {"left", "right", "<205>", "<206>", "<210>"} | OCR_TOGGLE_KEYS
# 按下时保持悬浮窗显示（不隐藏）的按键
KEEP_TOOLTIP_KEYS = {"y", "<198>"}
# 切换 Forza 全屏的按键
FULLSCREEN_TOGGLE_KEY = "<7>"
# 连续触发按键的防抖间隔（秒）
OCR_DEBOUNCE_SECONDS = 0.1
# OCR 前图像放大倍数（提升识别率）
OCR_UPSCALE_FACTOR = 2
# ---- 悬浮窗 ----
FONT_SIZE = 12
FONT_NAME = "Bahnschrift"
# 右侧结果为当前会话最大值时的高亮颜色
HIGHLIGHT_COLOR = "#ffe600"
# 各版本调校数值区域在 16:9 游戏画面内的相对位置（0~1）
OCR_REGION_RATIO = {
    "3": {"left": 0.394, "top": 0.333, "right": 0.618, "bottom": 0.518},
    "4": {"left": 0.419, "top": 0.333, "right": 0.613, "bottom": 0.503},
    "5": {"left": 0.718, "top": 0.358, "right": 0.882, "bottom": 0.495},
}
# 悬浮窗在 16:9 游戏画面内的固定锚点（相对位置 0~1），按游戏版本配置
TOOLTIP_ANCHORS = {
    "3": {"x": 0.50, "y": 0.630},
    "4": {"x": 0.50, "y": 0.601},
    "5": {"x": 0.50, "y": 0.630},
}
# 左右文本标签的水平锚点（relx），按游戏版本配置
TOOLTIP_LABEL_POS = {
    "3": (0.125, 0.199),
    "4": (0.138, 0.162),
    "5": (0.110, 0.252),
}