"""二次函数的纯函数：开口、对称轴、顶点、讲解、检查题、课程 JSON、自检。"""

from __future__ import annotations

TOLERANCE = 1e-9

A_ABS_MIN, A_ABS_MAX, A_DEFAULT = 0.5, 2.0, 1.0
H_MIN, H_MAX, H_DEFAULT = -3.0, 3.0, 0.0
K_MIN, K_MAX, K_DEFAULT = -3.0, 3.0, 0.0

FORMULA = "y = a(x − h)² + k"
CAUSAL = [
    "a 决定开口方向和大小。a>0 开口向上，a<0 开口向下；|a| 越大，开口越窄。",
    "h 决定对称轴 x = h。h 增大，对称轴向右移动；h 减小，向左移动。",
    "k 决定顶点的高低。k 增大，顶点向上移动；k 减小，向下移动。",
]
MISSING_NOTE = "图上未标出参数，先按 a=1，h=0，k=0 讲这个知识点。"


def format_number(value: float) -> str:
    number = round(float(value), 6)
    nearest = round(number)
    if abs(number - nearest) <= TOLERANCE:
        return str(int(nearest))
    return f"{number:.6f}".rstrip("0").rstrip(".")


def _clamp(value: float, low: float, high: float) -> float:
    return min(high, max(low, float(value)))


def clamp_a(raw) -> tuple[float, bool]:
    """返回采用值和是否夹取。0 没有方向，改用默认 1。"""
    if raw is None:
        return A_DEFAULT, False
    number = float(raw)
    if abs(number) <= TOLERANCE:
        return A_DEFAULT, True
    sign = 1.0 if number > 0 else -1.0
    magnitude = _clamp(abs(number), A_ABS_MIN, A_ABS_MAX)
    adopted = sign * magnitude
    changed = abs(adopted - number) > TOLERANCE
    return adopted, changed


def clamp_shift(raw, low: float, high: float, default: float) -> tuple[float, bool]:
    if raw is None:
        return default, False
    number = float(raw)
    adopted = _clamp(number, low, high)
    return adopted, abs(adopted - number) > TOLERANCE


def resolve_params(raw_a, raw_h, raw_k) -> tuple[float, float, float, str | None]:
    if raw_a is None and raw_h is None and raw_k is None:
        return A_DEFAULT, H_DEFAULT, K_DEFAULT, MISSING_NOTE
    amplitude, a_changed = clamp_a(raw_a)
    horizontal, h_changed = clamp_shift(raw_h, H_MIN, H_MAX, H_DEFAULT)
    vertical, k_changed = clamp_shift(raw_k, K_MIN, K_MAX, K_DEFAULT)
    missing = []
    if raw_a is None:
        missing.append(("a", A_DEFAULT))
    if raw_h is None:
        missing.append(("h", H_DEFAULT))
    if raw_k is None:
        missing.append(("k", K_DEFAULT))
    changed = a_changed or h_changed or k_changed
    if not changed and not missing:
        return amplitude, horizontal, vertical, None
    if not missing:
        original = (
            f"a={format_number(float(raw_a))}，"
            f"h={format_number(float(raw_h))}，"
            f"k={format_number(float(raw_k))}"
        )
        adopted = (
            f"a={format_number(amplitude)}，h={format_number(horizontal)}，k={format_number(vertical)}"
        )
        return (
            amplitude,
            horizontal,
            vertical,
            f"图上的参数已夹到可画范围。原值 {original}，采用 {adopted}。",
        )
    parts = []
    if changed:
        given = []
        adopted_bits = []
        if raw_a is not None:
            given.append(f"a={format_number(float(raw_a))}")
            adopted_bits.append(f"a={format_number(amplitude)}")
        if raw_h is not None:
            given.append(f"h={format_number(float(raw_h))}")
            adopted_bits.append(f"h={format_number(horizontal)}")
        if raw_k is not None:
            given.append(f"k={format_number(float(raw_k))}")
            adopted_bits.append(f"k={format_number(vertical)}")
        parts.append(
            "图上的参数已夹到可画范围。原值 "
            + "，".join(given)
            + "，采用 "
            + "，".join(adopted_bits)
            + "。"
        )
    shown = "、".join(label for label, _default in missing)
    defaults = "，".join(f"{label}={format_number(default)}" for label, default in missing)
    parts.append(f"图上未标出 {shown}，先按 {defaults}。")
    return amplitude, horizontal, vertical, "".join(parts)


def reading_params(raw_a, raw_h, raw_k, raw_b=None, raw_c=None):
    """一般式 y=ax²+bx+c 在代码里换成顶点式，再夹进可画范围。"""
    if (
        raw_h is None
        and raw_k is None
        and raw_a is not None
        and raw_b is not None
        and raw_c is not None
    ):
        try:
            amplitude = float(raw_a)
            linear = float(raw_b)
            constant = float(raw_c)
        except (TypeError, ValueError):
            amplitude = 0.0
            linear = 0.0
            constant = 0.0
        if abs(amplitude) > TOLERANCE:
            raw_h = -linear / (2 * amplitude)
            raw_k = constant - (linear * linear) / (4 * amplitude)
    return resolve_params(raw_a, raw_h, raw_k)


def opening_word(amplitude: float) -> str:
    if amplitude > TOLERANCE:
        return "向上"
    if amplitude < -TOLERANCE:
        return "向下"
    raise ValueError("a 不能为 0")


def next_a(amplitude: float) -> float:
    sign = 1.0 if amplitude > 0 else -1.0
    if abs(abs(amplitude) - A_ABS_MAX) > TOLERANCE:
        return sign * A_ABS_MAX
    return sign * 1.0


def next_h(horizontal: float) -> float:
    if abs(horizontal - 2.0) > TOLERANCE:
        return 2.0
    return -2.0


def next_k(vertical: float) -> float:
    if abs(vertical - 2.0) > TOLERANCE:
        return 2.0
    return -2.0


def build_checks(amplitude: float, horizontal: float, vertical: float) -> list[dict]:
    amplitude_2 = next_a(amplitude)
    wider = abs(amplitude_2) < abs(amplitude) - TOLERANCE
    width_answer = 0 if wider else 1
    width_explain = "|a| 越大，抛物线开口越窄；|a| 越小，开口越宽。"

    horizontal_2 = next_h(horizontal)
    axis_answer = 1 if horizontal_2 > horizontal else 0
    axis_explain = "对称轴是直线 x = h。h 增大，对称轴向右移动；h 减小，向左移动。"

    vertical_2 = next_k(vertical)
    vertex_answer = 1 if vertical_2 > vertical else 0
    vertex_explain = "顶点的纵坐标是 k。k 增大，顶点向上移动；k 减小，向下移动。"

    return [
        {
            "id": "c1",
            "prompt": (
                f"a 从 {format_number(amplitude)} 改为 {format_number(amplitude_2)}，"
                "其他不变。开口怎么变？"
            ),
            "choices": ["变宽", "变窄", "不变"],
            "answer": width_answer,
            "explain": width_explain,
        },
        {
            "id": "c2",
            "prompt": (
                f"h 从 {format_number(horizontal)} 改为 {format_number(horizontal_2)}，"
                "对称轴向哪边移动？"
            ),
            "choices": ["向左", "向右", "不动"],
            "answer": axis_answer,
            "explain": axis_explain,
        },
        {
            "id": "c3",
            "prompt": (
                f"k 从 {format_number(vertical)} 改为 {format_number(vertical_2)}，"
                "顶点向上还是向下移动？"
            ),
            "choices": ["向下", "向上", "不动"],
            "answer": vertex_answer,
            "explain": vertex_explain,
        },
    ]


def _axis_sentence(horizontal: float) -> str:
    text = format_number(horizontal)
    if horizontal > TOLERANCE:
        return f"对称轴在 y 轴右侧，x = {text}。"
    if horizontal < -TOLERANCE:
        return f"对称轴在 y 轴左侧，x = {text}。"
    return "对称轴就是 y 轴，x = 0。"


def _vertex_sentence(vertical: float) -> str:
    text = format_number(vertical)
    if vertical > TOLERANCE:
        return f"顶点向上离开 x 轴，y = {text}。"
    if vertical < -TOLERANCE:
        return f"顶点向下离开 x 轴，y = {text}。"
    return "顶点在 x 轴上，y = 0。"


def build_beats(amplitude: float, horizontal: float, vertical: float) -> list[dict]:
    a_text = format_number(amplitude)
    h_text = format_number(horizontal)
    k_text = format_number(vertical)
    word = opening_word(amplitude)
    return [
        {
            "id": "b1",
            "title": "从 y = x² 出发",
            "focus": "vertex",
            "narration": (
                "先看 y = x²：顶点在原点，开口向上，对称轴是 y 轴。"
                f"放上 a、h、k 之后，顶点是 ({h_text}, {k_text})。"
            ),
        },
        {
            "id": "b2",
            "title": "开口 a",
            "focus": "a",
            "narration": (
                f"a 决定开口方向和开口大小。当前 a = {a_text}。开口{word}。"
                f"|a| = {format_number(abs(amplitude))}，|a| 越大，开口越窄。"
            ),
        },
        {
            "id": "b3",
            "title": "对称轴 h",
            "focus": "h",
            "narration": f"h 决定对称轴。当前 h = {h_text}。{_axis_sentence(horizontal)}",
        },
        {
            "id": "b4",
            "title": "顶点高低 k",
            "focus": "k",
            "narration": f"k 决定顶点的高低。当前 k = {k_text}。{_vertex_sentence(vertical)}",
        },
    ]


def build_lesson(amplitude: float, horizontal: float, vertical: float, lesson_id: str, parameter_note) -> dict:
    return {
        "id": lesson_id,
        "title": f"二次函数 {FORMULA}",
        "subtitle": "人教A版必修第一册 · 第二章 一元二次函数、方程和不等式",
        "grade": "高一",
        "subject": "数学",
        "conceptFamily": "quadratic",
        "parameterNote": parameter_note,
        "recognition": {"confident": True, "asked": None},
        "formula": FORMULA,
        "causal": list(CAUSAL),
        "beats": build_beats(amplitude, horizontal, vertical),
        "animation": {
            "type": "quadratic",
            "domain": [-6, 6],
            "range": [-8, 8],
            "params": [
                {
                    "key": "a",
                    "label": "a",
                    "name": "开口",
                    "min": -A_ABS_MAX,
                    "max": A_ABS_MAX,
                    "step": 0.1,
                    "value": amplitude,
                },
                {
                    "key": "h",
                    "label": "h",
                    "name": "对称轴",
                    "min": H_MIN,
                    "max": H_MAX,
                    "step": 0.5,
                    "value": horizontal,
                },
                {
                    "key": "k",
                    "label": "k",
                    "name": "顶点高低",
                    "min": K_MIN,
                    "max": K_MAX,
                    "step": 0.5,
                    "value": vertical,
                },
            ],
        },
        "checks": build_checks(amplitude, horizontal, vertical),
    }


def _params_of(lesson: dict) -> tuple[float, float, float]:
    found = {}
    for item in (lesson.get("animation") or {}).get("params") or []:
        if isinstance(item, dict) and "key" in item:
            found[item["key"]] = item.get("value")
    return float(found["a"]), float(found["h"]), float(found["k"])


def inspect_lesson(lesson: dict) -> tuple[bool, str]:
    if not isinstance(lesson, dict):
        return False, "课程不是对象"
    try:
        amplitude, horizontal, vertical = _params_of(lesson)
    except (TypeError, ValueError, KeyError):
        return False, "参数无法读取"
    animation = lesson.get("animation") or {}
    if animation.get("type") != "quadratic":
        return False, "animation.type 不是 quadratic"
    if abs(amplitude) < A_ABS_MIN - TOLERANCE or abs(amplitude) > A_ABS_MAX + TOLERANCE:
        return False, "a 不在合法范围"
    if not (H_MIN - TOLERANCE <= horizontal <= H_MAX + TOLERANCE):
        return False, "h 不在合法范围"
    if not (K_MIN - TOLERANCE <= vertical <= K_MAX + TOLERANCE):
        return False, "k 不在合法范围"
    beats = lesson.get("beats")
    if not isinstance(beats, list):
        return False, "缺少四步讲解"
    found = {}
    for beat in beats:
        if isinstance(beat, dict) and isinstance(beat.get("id"), str):
            found[beat["id"]] = beat
    expected_focus = (("b1", "vertex"), ("b2", "a"), ("b3", "h"), ("b4", "k"))
    for beat_id, focus in expected_focus:
        beat = found.get(beat_id)
        if not isinstance(beat, dict) or beat.get("focus") != focus:
            return False, f"缺少讲解 {beat_id}"
        if not isinstance(beat.get("narration"), str):
            return False, f"{beat_id} 没有讲解正文"
    for beat in build_beats(amplitude, horizontal, vertical):
        if found[beat["id"]].get("narration") != beat["narration"]:
            return False, f"{beat['id']} 正文与当前参数不一致"
    opening = found["b2"]["narration"]
    word = opening_word(amplitude)
    other = "向下" if word == "向上" else "向上"
    if word not in opening or other in opening:
        return False, "开口方向与 a 的正负不一致"
    if "|a| 越大，开口越窄" not in opening:
        return False, "没有写开口随 |a| 变窄"
    axis = found["b3"]["narration"]
    if horizontal > TOLERANCE:
        if "右侧" not in axis or "左" in axis:
            return False, "h>0 时对称轴应在右侧"
    elif horizontal < -TOLERANCE:
        if "左侧" not in axis or "右" in axis:
            return False, "h<0 时对称轴应在左侧"
    elif "就是 y 轴" not in axis or "左" in axis or "右" in axis:
        return False, "h=0 时对称轴应是 y 轴"
    vertex = found["b4"]["narration"]
    if vertical > TOLERANCE:
        if "向上" not in vertex or "向下" in vertex:
            return False, "k>0 时顶点应向上"
    elif vertical < -TOLERANCE:
        if "向下" not in vertex or "向上" in vertex:
            return False, "k<0 时顶点应向下"
    elif "在 x 轴上" not in vertex:
        return False, "k=0 时顶点应在 x 轴上"
    expected_checks = build_checks(amplitude, horizontal, vertical)
    if lesson.get("checks") != expected_checks:
        return False, "检查题没有按当前参数重算"
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
