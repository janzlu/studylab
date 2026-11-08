"""对数函数的纯函数：单调性、定点、倒数对称、讲解、检查题、自检。"""

from __future__ import annotations

TOLERANCE = 1e-9

LOW_MIN, LOW_MAX = 0.25, 0.8
HIGH_MIN, HIGH_MAX = 1.25, 4.0
DEFAULT_BASE = 2.0

FORMULA = "y = logₐ(x)"
CAUSAL = [
    "a>1 时函数递增，0<a<1 时函数递减。",
    "不论底数取允许的值，图像都过定点 (1, 0)。",
    "底数换成倒数后，log 的值变号，图像关于 x 轴对称。",
]
MISSING_NOTE = "图上未标出参数，先按 a=2 讲这个知识点。"


def format_number(value: float) -> str:
    number = round(float(value), 6)
    nearest = round(number)
    if abs(number - nearest) <= TOLERANCE:
        return str(int(nearest))
    return f"{number:.6f}".rstrip("0").rstrip(".")


def clamp_base(raw) -> tuple[float, bool]:
    """合法底数落在 [0.25, 0.8] 或 [1.25, 4]。1 和负数改用 2。"""
    if raw is None:
        return DEFAULT_BASE, False
    number = float(raw)
    if number <= 0 or abs(number - 1) <= 1e-6:
        return DEFAULT_BASE, True
    if number < 1:
        adopted = min(LOW_MAX, max(LOW_MIN, number))
    else:
        adopted = min(HIGH_MAX, max(HIGH_MIN, number))
    return adopted, abs(adopted - number) > TOLERANCE


def resolve_params(raw_base) -> tuple[float, str | None]:
    if raw_base is None:
        return DEFAULT_BASE, MISSING_NOTE
    base, changed = clamp_base(raw_base)
    if not changed:
        return base, None
    return base, (
        f"图上的底数已夹到可画范围。原值 a={format_number(float(raw_base))}，"
        f"采用 a={format_number(base)}。"
    )


def other_base(base: float) -> float:
    """换到 1 的另一侧，用来问单调性。"""
    if base > 1:
        return 0.5
    return 2.0


def monotonic_word(base: float) -> str:
    if base > 1:
        return "递增"
    if 0 < base < 1:
        return "递减"
    raise ValueError("底数不合法")


def build_checks(base: float) -> list[dict]:
    flipped = other_base(base)
    flipped_word = monotonic_word(flipped)
    mono_answer = 0 if flipped_word == "递增" else 1
    mono_explain = "a>1 时函数递增。" if flipped > 1 else "0<a<1 时函数递减。"
    reciprocal = 1 / base
    return [
        {
            "id": "c1",
            "prompt": (
                f"a 从 {format_number(base)} 改为 {format_number(flipped)}，"
                "函数变为递增还是递减？"
            ),
            "choices": ["递增", "递减", "不变"],
            "answer": mono_answer,
            "explain": mono_explain,
        },
        {
            "id": "c2",
            "prompt": (
                f"a 从 {format_number(base)} 改为 {format_number(flipped)}，图像仍过哪个点？"
            ),
            "choices": ["(0, 1)", "(1, 0)", "(0, 0)"],
            "answer": 1,
            "explain": "a⁰ = 1，所以 logₐ(1) = 0。图像过 (1, 0)，不是指数函数的 (0, 1)。",
        },
        {
            "id": "c3",
            "prompt": (
                f"a 从 {format_number(base)} 换成它的倒数 {format_number(reciprocal)}，"
                "图像关于哪条直线对称？"
            ),
            "choices": ["y 轴", "x 轴", "直线 y = x"],
            "answer": 1,
            "explain": "log 的底数换成倒数后，函数值变号，图像关于 x 轴对称。",
        },
    ]


def build_beats(base: float) -> list[dict]:
    text = format_number(base)
    word = monotonic_word(base)
    if base > 1:
        mono = f"当前 a = {text}。a>1，函数{word}。"
    else:
        mono = f"当前 a = {text}。0<a<1，函数{word}。"
    reciprocal = format_number(1 / base)
    return [
        {
            "id": "b1",
            "title": "对数在说什么",
            "focus": "domain",
            "narration": (
                "aʸ = x 时，y 就是 logₐ(x)。定义域是 x>0。"
                "图像只出现在 y 轴右侧，y 轴是渐近线。"
            ),
        },
        {
            "id": "b2",
            "title": "底数与单调性",
            "focus": "mono",
            "narration": mono,
        },
        {
            "id": "b3",
            "title": "定点",
            "focus": "point",
            "narration": "不论底数取允许的值，图像都过定点 (1, 0)。因为任何允许的 a 都满足 a⁰ = 1。",
        },
        {
            "id": "b4",
            "title": "换成倒数",
            "focus": "reciprocal",
            "narration": (
                f"把底数 {text} 换成倒数 {reciprocal}。函数值变号，图像关于 x 轴对称。"
            ),
        },
    ]


def build_lesson(base: float, lesson_id: str, parameter_note) -> dict:
    return {
        "id": lesson_id,
        "title": f"对数函数 {FORMULA}",
        "subtitle": "人教A版必修第一册 · 第四章 指数函数与对数函数",
        "grade": "高一",
        "subject": "数学",
        "conceptFamily": "logarithm",
        "parameterNote": parameter_note,
        "recognition": {"confident": True, "asked": None},
        "formula": FORMULA,
        "causal": list(CAUSAL),
        "beats": build_beats(base),
        "animation": {
            "type": "logarithm",
            "domain": [0.15, 8],
            "range": [-4, 4],
            "params": [
                {
                    "key": "base",
                    "label": "a",
                    "name": "底数",
                    "min": LOW_MIN,
                    "max": HIGH_MAX,
                    "step": 0.05,
                    "value": base,
                }
            ],
        },
        "checks": build_checks(base),
    }


def _base_of(lesson: dict) -> float:
    for item in (lesson.get("animation") or {}).get("params") or []:
        if isinstance(item, dict) and item.get("key") == "base":
            return float(item["value"])
    raise KeyError("base")


def inspect_lesson(lesson: dict) -> tuple[bool, str]:
    if not isinstance(lesson, dict):
        return False, "课程不是对象"
    try:
        base = _base_of(lesson)
    except (TypeError, ValueError, KeyError):
        return False, "参数无法读取"
    if not (0 < base < 1 or base > 1):
        return False, "底数不合法"
    low_ok = LOW_MIN - TOLERANCE <= base <= LOW_MAX + TOLERANCE
    high_ok = HIGH_MIN - TOLERANCE <= base <= HIGH_MAX + TOLERANCE
    if not (low_ok or high_ok):
        return False, "底数不在可画范围"
    animation = lesson.get("animation") or {}
    if animation.get("type") != "logarithm":
        return False, "animation.type 不是 logarithm"
    beats = {beat.get("id"): beat for beat in lesson.get("beats") or [] if isinstance(beat, dict)}
    expected = (("b1", "domain"), ("b2", "mono"), ("b3", "point"), ("b4", "reciprocal"))
    for beat_id, focus in expected:
        beat = beats.get(beat_id)
        if not isinstance(beat, dict) or beat.get("focus") != focus:
            return False, f"缺少讲解 {beat_id}"
        if not isinstance(beat.get("narration"), str):
            return False, f"{beat_id} 没有讲解正文"
    for beat in build_beats(base):
        if beats[beat["id"]].get("narration") != beat["narration"]:
            return False, f"{beat['id']} 正文与当前参数不一致"
    mono = beats["b2"]["narration"]
    word = monotonic_word(base)
    other = "递减" if word == "递增" else "递增"
    if word not in mono or other in mono:
        return False, "单调性与底数不一致"
    point = beats["b3"]["narration"]
    if "(1, 0)" not in point or "(0, 1)" in point:
        return False, "定点应是 (1, 0)"
    reciprocal = beats["b4"]["narration"]
    if "x 轴" not in reciprocal or "y 轴" in reciprocal or "y = x" in reciprocal:
        return False, "倒数对称应关于 x 轴"
    expected_checks = build_checks(base)
    if lesson.get("checks") != expected_checks:
        return False, "检查题没有按当前底数重算"
    for item in expected_checks:
        answer = item["answer"]
        choices = item["choices"]
        if isinstance(answer, bool) or not isinstance(answer, int):
            return False, "答案下标不是整数"
        if answer < 0 or answer >= len(choices):
            return False, "答案下标越界"
        if choices.count(choices[answer]) != 1:
            return False, "正确选项不唯一"
    return True, ""


def self_check(lesson: dict) -> bool:
    try:
        ok, _reason = inspect_lesson(lesson)
    except Exception:
        return False
    return ok
