"""三角函数的纯函数：单位圆上的正弦、余弦、正切。

只讲同一个角的 sin、cos、tan。正弦型函数 y = A sin(ωx + φ) 是另一节。
"""

from __future__ import annotations

import math

from logarithm import TOLERANCE, format_number

THETA_MIN, THETA_MAX, THETA_DEFAULT = 0.0, 6.28, 1.05
AXIS_TOLERANCE = 1e-6

FORMULA = "sin θ，cos θ，tan θ"
CAUSAL = [
    "单位圆上，角 θ 的终边交点是 (cos θ, sin θ)。",
    "sin θ 是纵坐标，cos θ 是横坐标，并且 sin²θ + cos²θ = 1。",
    "tan θ = sin θ / cos θ。cos θ = 0 时，tan θ 没有定义。",
]
MISSING_NOTE = "图上未标出角，先按 θ=1.05 讲这个知识点。"


def resolve_params(raw_theta, unit=None) -> tuple[float, str | None]:
    """unit 为 deg 时按角度换算。未标明单位、且数值大于一圈时，也按角度处理。"""
    if raw_theta is None:
        return THETA_DEFAULT, MISSING_NOTE
    number = float(raw_theta)
    original = format_number(number)
    marked = unit if unit in {"rad", "deg"} else None
    from_degrees = marked == "deg" or (
        marked is None and number > THETA_MAX + TOLERANCE and number <= 360
    )
    if from_degrees:
        number = number * math.pi / 180
    adopted = min(THETA_MAX, max(THETA_MIN, number))
    if from_degrees:
        return adopted, f"图上的角按角度换算。原值 {original}°，采用 θ={format_number(adopted)}。"
    if abs(adopted - number) > TOLERANCE:
        return adopted, (
            f"图上的角已夹到可画范围。原值 θ={original}，采用 θ={format_number(adopted)}。"
        )
    return adopted, None


def sin_word(theta: float) -> str:
    value = math.sin(theta)
    if abs(value) <= AXIS_TOLERANCE:
        return "零"
    if value > 0:
        return "正"
    return "负"


def tan_sentence(theta: float) -> str:
    cosine = math.cos(theta)
    if abs(cosine) <= AXIS_TOLERANCE:
        return "cos θ = 0，tan θ 没有定义。"
    return f"当前 tan θ = {format_number(math.tan(theta))}。"


def build_checks(theta: float) -> list[dict]:
    text = format_number(theta)
    word = sin_word(theta)
    sign_answer = {"正": 0, "负": 1, "零": 2}[word]
    sign_explain = {
        "正": "这个角的终边在 x 轴上方，sin θ 是正的。",
        "负": "这个角的终边在 x 轴下方，sin θ 是负的。",
        "零": "终边落在 x 轴上，sin θ = 0。",
    }[word]
    return [
        {
            "id": "c1",
            "prompt": f"当前 θ = {text}。sin²θ + cos²θ 等于多少？",
            "choices": ["0", "1", "tan θ"],
            "answer": 1,
            "explain": "单位圆上横坐标、纵坐标满足 x² + y² = 1，也就是 cos²θ + sin²θ = 1。",
        },
        {
            "id": "c2",
            "prompt": "cos θ 是单位圆上对应点的哪个坐标？",
            "choices": ["纵坐标", "横坐标", "到原点的距离"],
            "answer": 1,
            "explain": "对应点是 (cos θ, sin θ)。横坐标是 cos θ，纵坐标是 sin θ。",
        },
        {
            "id": "c3",
            "prompt": f"当前 θ = {text}。sin θ 是正、负还是零？",
            "choices": ["正", "负", "零"],
            "answer": sign_answer,
            "explain": sign_explain,
        },
    ]


def build_beats(theta: float) -> list[dict]:
    text = format_number(theta)
    sine = format_number(math.sin(theta))
    cosine = format_number(math.cos(theta))
    return [
        {
            "id": "b1",
            "title": "单位圆上的角",
            "focus": "circle",
            "narration": (
                f"角 θ 的始边在 x 轴正方向，终边逆时针转到 θ。当前 θ = {text}。"
                "终边和单位圆的交点是 (cos θ, sin θ)。"
            ),
        },
        {
            "id": "b2",
            "title": "正弦",
            "focus": "sin",
            "narration": f"sin θ 是这个点的纵坐标。当前 sin θ = {sine}。",
        },
        {
            "id": "b3",
            "title": "余弦",
            "focus": "cos",
            "narration": (
                f"cos θ 是这个点的横坐标。当前 cos θ = {cosine}。"
                "并且 sin²θ + cos²θ = 1。"
            ),
        },
        {
            "id": "b4",
            "title": "正切",
            "focus": "tan",
            "narration": (
                f"tan θ = sin θ / cos θ。当前 cos θ = {cosine}。{tan_sentence(theta)}"
            ),
        },
    ]


def build_lesson(theta: float, lesson_id: str, parameter_note) -> dict:
    return {
        "id": lesson_id,
        "title": f"三角函数 {FORMULA}",
        "subtitle": "人教A版必修第一册 · 第五章 三角函数的定义",
        "grade": "高一",
        "subject": "数学",
        "conceptFamily": "trig",
        "parameterNote": parameter_note,
        "recognition": {"confident": True, "asked": None},
        "formula": FORMULA,
        "causal": list(CAUSAL),
        "beats": build_beats(theta),
        "animation": {
            "type": "trig",
            "domain": [-1.4, 1.4],
            "range": [-1.4, 1.4],
            "params": [
                {
                    "key": "theta",
                    "label": "θ",
                    "name": "角",
                    "min": THETA_MIN,
                    "max": THETA_MAX,
                    "step": 0.01,
                    "value": theta,
                }
            ],
        },
        "checks": build_checks(theta),
    }


def _theta_of(lesson: dict) -> float:
    for item in (lesson.get("animation") or {}).get("params") or []:
        if isinstance(item, dict) and item.get("key") == "theta":
            return float(item["value"])
    raise KeyError("theta")


def inspect_lesson(lesson: dict) -> tuple[bool, str]:
    if not isinstance(lesson, dict):
        return False, "课程不是对象"
    try:
        theta = _theta_of(lesson)
    except (TypeError, ValueError, KeyError):
        return False, "参数无法读取"
    if not (THETA_MIN - TOLERANCE <= theta <= THETA_MAX + TOLERANCE):
        return False, "θ 不在可画范围"
    animation = lesson.get("animation") or {}
    if animation.get("type") != "trig":
        return False, "animation.type 不是 trig"
    beats = {beat.get("id"): beat for beat in lesson.get("beats") or [] if isinstance(beat, dict)}
    expected = (("b1", "circle"), ("b2", "sin"), ("b3", "cos"), ("b4", "tan"))
    for beat_id, focus in expected:
        beat = beats.get(beat_id)
        if not isinstance(beat, dict) or beat.get("focus") != focus:
            return False, f"缺少讲解 {beat_id}"
        if not isinstance(beat.get("narration"), str):
            return False, f"{beat_id} 没有讲解正文"
    for beat in build_beats(theta):
        if beats[beat["id"]].get("narration") != beat["narration"]:
            return False, f"{beat['id']} 正文与当前参数不一致"
    sine = format_number(math.sin(theta))
    cosine = format_number(math.cos(theta))
    if f"当前 sin θ = {sine}" not in beats["b2"]["narration"]:
        return False, "正弦数值与 θ 不一致"
    if f"当前 cos θ = {cosine}" not in beats["b3"]["narration"]:
        return False, "余弦数值与 θ 不一致"
    tangent = beats["b4"]["narration"]
    if abs(math.cos(theta)) <= AXIS_TOLERANCE:
        if "没有定义" not in tangent:
            return False, "cos θ = 0 时正切应没有定义"
    elif f"当前 tan θ = {format_number(math.tan(theta))}" not in tangent:
        return False, "正切数值与 θ 不一致"
    expected_checks = build_checks(theta)
    if lesson.get("checks") != expected_checks:
        return False, "检查题没有按当前角重算"
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
