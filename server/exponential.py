"""指数函数的纯函数：单调性、定点、倒数对称、讲解、检查题、自检。

只讲 y = aˣ。对数函数是另一节，这里不画、不讲它的性质。
"""

from __future__ import annotations

from logarithm import (
    HIGH_MAX,
    HIGH_MIN,
    LOW_MAX,
    LOW_MIN,
    TOLERANCE,
    format_number,
    monotonic_word,
    other_base,
)
from logarithm import resolve_params as _resolve_base


def resolve_params(raw_base):
    """底数的夹取与对数函数相同，说明仍只谈指数函数这一节。"""
    return _resolve_base(raw_base)

FORMULA = "y = aˣ"
CAUSAL = [
    "a>1 时函数递增，0<a<1 时函数递减。",
    "不论底数取允许的值，图像都过定点 (0, 1)。",
    "底数换成倒数后，图像关于 y 轴对称。",
]


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
            "choices": ["(1, 0)", "(0, 1)", "(0, 0)"],
            "answer": 1,
            "explain": "a⁰ = 1，所以图像过 (0, 1)。",
        },
        {
            "id": "c3",
            "prompt": (
                f"a 从 {format_number(base)} 换成它的倒数 {format_number(reciprocal)}，"
                "图像关于哪条直线对称？"
            ),
            "choices": ["x 轴", "y 轴", "直线 y = x"],
            "answer": 1,
            "explain": "底数换成倒数后，aˣ 变成 a 的负指数，图像关于 y 轴对称。",
        },
    ]


def build_beats(base: float) -> list[dict]:
    text = format_number(base)
    word = monotonic_word(base)
    reciprocal = format_number(1 / base)
    if base > 1:
        mono = f"当前 a = {text}。a>1，函数{word}。"
    else:
        mono = f"当前 a = {text}。0<a<1，函数{word}。"
    return [
        {
            "id": "b1",
            "title": "指数在说什么",
            "focus": "domain",
            "narration": (
                "指数函数是 y = aˣ。定义域是全体实数，值域是 y>0。"
                "x 轴是水平渐近线，图像在 x 轴上方。"
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
            "narration": "不论底数取允许的值，图像都过定点 (0, 1)。因为任何允许的 a 都满足 a⁰ = 1。",
        },
        {
            "id": "b4",
            "title": "换成倒数",
            "focus": "reciprocal",
            "narration": f"把底数 {text} 换成倒数 {reciprocal}。图像关于 y 轴对称。",
        },
    ]


def build_lesson(base: float, lesson_id: str, parameter_note) -> dict:
    return {
        "id": lesson_id,
        "title": f"指数函数 {FORMULA}",
        "subtitle": "人教A版必修第一册 · 第四章 指数函数",
        "grade": "高一",
        "subject": "数学",
        "conceptFamily": "exponential",
        "parameterNote": parameter_note,
        "recognition": {"confident": True, "asked": None},
        "formula": FORMULA,
        "causal": list(CAUSAL),
        "beats": build_beats(base),
        "animation": {
            "type": "exponential",
            "domain": [-2, 4],
            "range": [-1, 4],
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
    if animation.get("type") != "exponential":
        return False, "animation.type 不是 exponential"
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
    if "(0, 1)" not in point or "(1, 0)" in point:
        return False, "定点应是 (0, 1)"
    reciprocal = beats["b4"]["narration"]
    if "y 轴" not in reciprocal or "x 轴" in reciprocal or "y = x" in reciprocal:
        return False, "倒数对称应关于 y 轴"
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
