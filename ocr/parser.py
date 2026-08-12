"""OCR 文本解析：提取数字并计算调校比值。"""

from dataclasses import dataclass

# 各版本调校数值在 OCR 数字序列中的下标映射 (a, b, c, d)
# 新比值 = c ÷ d，旧比值 = a ÷ b
RATIO_INDEX_MAP = {
    "3": (0, 2, 3, 5),
    "4": (0, 4, 2, 5),
    "5": (0, 4, 1, 5),
}

# OCR 常见误识别字符 → 正确数字（空串表示直接丢弃）
CHAR_MAP = {
    "A": "4",
    "T": "7",
    "o": "0",
    ",": "",
    ".": "",
}


def read_numbers(text):
    """从 OCR 文本中提取长度大于 1 的连续数字序列，并进行字符纠错。"""
    numbers = []
    buffer = []
    for char in text:
        if char.isnumeric():
            buffer.append(char)
        elif char in CHAR_MAP:
            mapped = CHAR_MAP[char]
            if mapped:
                buffer.append(mapped)
        elif buffer:
            if len(buffer) > 1:
                numbers.append("".join(buffer))
            buffer = []
    if buffer and len(buffer) > 1:
        numbers.append("".join(buffer))
    return numbers


def calc_ratio_str(a, b):
    """计算 a ÷ b 并格式化为五位小数（去除前导 0），失败返回 "0"。"""
    try:
        return format(int(a) / int(b), ".5f").replace("0.", ".")
    except (ValueError, ZeroDivisionError):
        return "0"


@dataclass
class RatioResult:
    """一次调校数值的解析结果。"""

    old_ratio: str
    new_ratio: str
    a: str
    b: str
    c: str
    d: str

    @property
    def new_value(self) -> float:
        """新比值的数值形式，用于会话最大值比较；解析失败返回 0.0。"""
        try:
            text = self.new_ratio if self.new_ratio.startswith("0") else f"0{self.new_ratio}"
            return float(text)
        except ValueError:
            return 0.0


def parse_ratio(text, version):
    """从 OCR 文本解析新旧比值；数字数量不符时返回 None。"""
    numbers = read_numbers(text)
    if len(numbers) != 6:
        print(f"Unexpected number of values ({len(numbers)}):\n{text}")
        return None

    ia, ib, ic, id_ = RATIO_INDEX_MAP.get(version, RATIO_INDEX_MAP["3"])
    a, b, c, d = numbers[ia], numbers[ib], numbers[ic], numbers[id_]
    return RatioResult(
        old_ratio=calc_ratio_str(a, b),
        new_ratio=calc_ratio_str(c, d),
        a=a, b=b, c=c, d=d,
    )