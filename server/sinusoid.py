"""正弦型函数的纯函数：周期、方向、夹取、讲解、检查题、课程 JSON、自检。"""

from __future__ import annotations

import math
from fractions import Fraction

TOLERANCE = 1e-9
PERIOD_TOLERANCE = 1e-6

A_MIN, A_MAX, A_DEFAULT = 0.5, 2.5, 1.0
OMEGA_MIN, OMEGA_MAX, OMEGA_DEFAULT = 0.5, 3.0, 1.0
PHI_MIN, PHI_MAX, PHI_DEFAULT = -3.14, 3.14, 0.0

CAUSAL = [
    "A 决定离开平衡位置的最大距离，不改变周期。",
    "ω 决定周期 T = 2π/|ω|。|ω| 变大，波变得更密。",
    "φ>0 时图像向左平移 φ/|ω|；φ<0 时向右平移；φ=0 时不平移。",
]

MISSING_NOTE = "图上未标出参数，先按 A=1，ω=1，φ=0 讲这个知识点。"


def period_value(omega: float) -> float:
    """T = 2π / |ω|。只跟 ω 有关。"""
    magnitude = abs(float(omega))
    if magnitude == 0:
        raise ValueError("ω 不能为 0")
    return 2 * math.pi / magnitude


def format_number(value: float) -> str:
    """整数不带小数，其余去掉尾部 0。"""
    number = round(float(value), 6)
    nearest = round(number)
    if abs(number - nearest) <= TOLERANCE:
        return str(int(nearest))
    return f"{number:.6f}".rstrip("0").rstrip(".")


def _pi_text(numerator: int, denominator: int) -> str:
    numerator = abs(int(numerator))
    denominator = int(denominator)
    if denominator == 1:
        if numerator == 1:
            return "π"
        return f"{numerator}π"
    if numerator == 1:
        return f"π/{denominator}"
    return f"{numerator}π/{denominator}"


def format_period(omega: float) -> str:
    """把 T = 2π/|ω| 写成 nπ/d；误差不够小就用 6 位小数。

    假想角频率可以落在滑杆范围外，这里仍然计算。
    """
    magnitude = abs(float(omega))
    if magnitude == 0:
        raise ValueError("ω 不能为 0")
    true_period = 2 * math.pi / magnitude
    ratio = 2 / magnitude
    frac = Fraction(ratio).limit_denominator(100)
    approx_ratio = float(frac)
    approx_period = approx_ratio * math.pi
    ratio_ok = abs(approx_ratio - ratio) < PERIOD_TOLERANCE
    period_ok = abs(approx_period - true_period) < PERIOD_TOLERANCE
    if ratio_ok and period_ok:
        return _pi_text(frac.numerator, frac.denominator)
    return f"{true_period:.6f}"


def parse_period_text(text: str) -> float:
    """把 format_period 的结果还原成数值。"""
    body = text.strip()
    if "π" not in body:
        return float(body)
    if "/" in body:
        left, denom_text = body.split("/", 1)
        denominator = int(denom_text)
        if left == "π":
            numerator = 1
        else:
            numerator = int(left.replace("π", ""))
        return numerator / denominator * math.pi
    if body == "π":
        return math.pi
    return int(body.replace("π", "")) * math.pi


def shift_direction(phi: float) -> str:
    if phi > TOLERANCE:
        return "left"
    if phi < -TOLERANCE:
        return "right"
    return "none"


def shift_amount(phi: float, omega: float) -> float:
    return abs(float(phi)) / abs(float(omega))


def _clamp(value: float, low: float, high: float) -> float:
    if value < low:
        return low
    if value > high:
        return high
    return value


def resolve_params(raw_a, raw_omega, raw_phi):
    """缺的数字用默认值。给出的数字先夹进合法范围。

    返回 (A, omega, phi, parameterNote)。
    """
    specs = (
        ("A", raw_a, A_MIN, A_MAX, A_DEFAULT),
        ("ω", raw_omega, OMEGA_MIN, OMEGA_MAX, OMEGA_DEFAULT),
        ("φ", raw_phi, PHI_MIN, PHI_MAX, PHI_DEFAULT),
    )
    values = []
    notes = []
    missing = []
    any_given = False
    for label, raw, low, high, default in specs:
        if raw is None:
            values.append(default)
            missing.append((label, default))
            continue
        any_given = True
        original = float(raw)
        adopted = _clamp(original, low, high)
        if abs(adopted - original) > TOLERANCE:
            notes.append(
                f"{label} 原值 {format_number(original)}，采用 {format_number(adopted)}"
            )
        values.append(adopted)
    if not any_given:
        note = MISSING_NOTE
    else:
        if missing:
            shown = "、".join(label for label, _default in missing)
            defaults = "，".join(
                f"{label}={format_number(default)}" for label, default in missing
            )
            notes.append(f"图上未标出 {shown}，先按 {defaults}")
        note = "。".join(notes) + "。" if notes else None
    return values[0], values[1], values[2], note


def _canonical(value: float):
    number = float(value)
    nearest = round(number)
    if abs(number - nearest) <= TOLERANCE:
        return int(nearest)
    return number


def build_checks(amplitude: float, omega: float, phi: float) -> list[dict]:
    amplitude = float(amplitude)
    omega = float(omega)
    phi = float(phi)
    amplitude_next = 1.0 if abs(amplitude - 2) <= TOLERANCE else 2.0
    omega_next = 4.0 if abs(omega - 2) <= TOLERANCE else 2.0
    period_choices = [
        format_period(omega_next / 2),
        format_period(omega_next),
        format_period(omega_next * 2),
    ]
    if phi < -TOLERANCE:
        phase_prompt = "φ 从 0 改为负数，图像往哪边平移？"
        phase_choices = ["向左", "向右", "不平移"]
        phase_explain = "φ<0 时向右平移 |φ|/|ω|。"
    else:
        phase_prompt = "φ 从 0 改为正数，图像往哪边平移？"
        phase_choices = ["向右", "向左", "不平移"]
        phase_explain = "φ>0 时向左平移 φ/|ω|。"
    return [
        {
            "id": "c1",
            "prompt": (
                f"A 从 {format_number(amplitude)} 改为 {format_number(amplitude_next)}，"
                "其他不变。周期怎么变？"
            ),
            "choices": ["变为原来的 2 倍", "不变", "变为原来的一半"],
            "answer": 1,
            "explain": "周期 T = 2π/|ω|，只跟 ω 有关。",
        },
        {
            "id": "c2",
            "prompt": (
                f"ω 从 {format_number(omega)} 改为 {format_number(omega_next)}，"
                "周期是多少？"
            ),
            "choices": period_choices,
            "answer": 1,
            "explain": (
                "周期 T = 2π/|ω|。"
                f"ω 改为 {format_number(omega_next)} 后，T = {format_period(omega_next)}。"
            ),
        },
        {
            "id": "c3",
            "prompt": phase_prompt,
            "choices": phase_choices,
            "answer": 1,
            "explain": phase_explain,
        },
    ]


def _beat_narration(amplitude: float, omega: float, phi: float) -> list[dict]:
    period_text = format_period(omega)
    amplitude_text = format_number(amplitude)
    omega_text = format_number(omega)
    phi_text = format_number(phi)
    circle = (
        "单位圆上的点转到角 t，它的纵坐标就是 sin t。"
        "把这个高度沿横轴展开，得到正弦波。"
        f"当前 A = {amplitude_text}，ω = {omega_text}，φ = {phi_text}。"
    )
    amplitude_line = (
        "A 把波峰和波谷拉高或压低，周期不变。"
        f"当前 A = {amplitude_text}。T = {period_text}。"
    )
    omega_line = (
        f"ω 改变角走得有多快。当前 ω = {omega_text}。T = {period_text}。"
    )
    direction = shift_direction(phi)
    if direction == "left":
        amount = format_number(phi / abs(omega))
        phase_line = (
            f"φ 是起步时的角度。当前 φ = {phi_text}。图像向左平移 {amount}。"
        )
    elif direction == "right":
        amount = format_number(abs(phi) / abs(omega))
        phase_line = (
            f"φ 是起步时的角度。当前 φ = {phi_text}。图像向右平移 {amount}。"
        )
    else:
        phase_line = "φ 是起步时的角度。当前 φ = 0。图像不平移。"
    return [
        {"id": "b1", "title": "从单位圆展开", "narration": circle, "focus": "circle"},
        {"id": "b2", "title": "振幅 A", "narration": amplitude_line, "focus": "A"},
        {"id": "b3", "title": "角频率与周期", "narration": omega_line, "focus": "omega"},
        {"id": "b4", "title": "初相", "narration": phase_line, "focus": "phi"},
    ]


def build_lesson(amplitude, omega, phi, lesson_id: str, parameter_note) -> dict:
    amplitude = float(amplitude)
    omega = float(omega)
    phi = float(phi)
    return {
        "id": lesson_id,
        "title": "正弦型函数 y = A sin(ωx + φ)",
        "subtitle": "人教A版必修第一册 · 第五章 三角函数",
        "grade": "高一",
        "subject": "数学",
        "conceptFamily": "sinusoid",
        "parameterNote": parameter_note,
        "recognition": {"confident": True, "asked": None},
        "formula": "y = A sin(ωx + φ)",
        "causal": list(CAUSAL),
        "beats": _beat_narration(amplitude, omega, phi),
        "animation": {
            "type": "sinusoid",
            "domain": [-6.2832, 6.2832],
            "range": [-3, 3],
            "params": [
                {
                    "key": "A",
                    "label": "A",
                    "name": "振幅",
                    "min": A_MIN,
                    "max": A_MAX,
                    "step": 0.1,
                    "value": _canonical(amplitude),
                },
                {
                    "key": "omega",
                    "label": "ω",
                    "name": "角频率",
                    "min": OMEGA_MIN,
                    "max": OMEGA_MAX,
                    "step": 0.1,
                    "value": _canonical(omega),
                },
                {
                    "key": "phi",
                    "label": "φ",
                    "name": "初相",
                    "min": PHI_MIN,
                    "max": PHI_MAX,
                    "step": 0.01,
                    "value": _canonical(phi),
                },
            ],
        },
        "checks": build_checks(amplitude, omega, phi),
    }


def lesson_for_reading(raw_a, raw_omega, raw_phi, lesson_id: str = "sinusoid-reading") -> dict:
    amplitude, omega, phi, note = resolve_params(raw_a, raw_omega, raw_phi)
    return build_lesson(amplitude, omega, phi, lesson_id, note)


def _params_of(lesson: dict) -> tuple[float, float, float]:
    animation = lesson.get("animation")
    if not isinstance(animation, dict):
        raise ValueError("缺少动画")
    found = {}
    for item in animation.get("params") or []:
        if isinstance(item, dict) and "key" in item:
            found[item["key"]] = item.get("value")
    return float(found["A"]), float(found["omega"]), float(found["phi"])


def inspect_lesson(lesson: dict) -> tuple[bool, str]:
    if not isinstance(lesson, dict):
        return False, "课程不是对象"
    try:
        amplitude, omega, phi = _params_of(lesson)
    except (TypeError, ValueError, KeyError):
        return False, "参数无法读取"
    animation = lesson["animation"]
    if animation.get("type") != "sinusoid":
        return False, "animation.type 不是 sinusoid"
    if not (A_MIN - TOLERANCE <= amplitude <= A_MAX + TOLERANCE) or amplitude <= 0:
        return False, "A 不在合法范围"
    if not (OMEGA_MIN - TOLERANCE <= omega <= OMEGA_MAX + TOLERANCE) or omega == 0:
        return False, "ω 不在合法范围"
    if not (PHI_MIN - TOLERANCE <= phi <= PHI_MAX + TOLERANCE):
        return False, "φ 不在合法范围"
    beats = lesson.get("beats")
    if not isinstance(beats, list):
        return False, "缺少四步讲解"
    found = {}
    for beat in beats:
        if isinstance(beat, dict) and isinstance(beat.get("id"), str):
            found[beat["id"]] = beat
    expected_focus = (
        ("b1", "circle"),
        ("b2", "A"),
        ("b3", "omega"),
        ("b4", "phi"),
    )
    for beat_id, focus in expected_focus:
        beat = found.get(beat_id)
        if not isinstance(beat, dict) or beat.get("focus") != focus:
            return False, f"缺少讲解 {beat_id}"
        if not isinstance(beat.get("narration"), str):
            return False, f"{beat_id} 没有讲解正文"
    try:
        period_text = format_period(omega)
        parsed = parse_period_text(period_text)
    except (TypeError, ValueError):
        return False, "周期文本无法计算"
    if abs(parsed - period_value(omega)) >= PERIOD_TOLERANCE:
        return False, "周期文本与 2π/|ω| 不一致"
    for beat in _beat_narration(amplitude, omega, phi):
        if found[beat["id"]].get("narration") != beat["narration"]:
            return False, f"{beat['id']} 正文与当前参数不一致"
    expected_checks = build_checks(amplitude, omega, phi)
    got_checks = lesson.get("checks")
    if got_checks != expected_checks:
        return False, "检查题没有按当前参数重算"
    for item in expected_checks:
        answer = item["answer"]
        choices = item["choices"]
        if isinstance(answer, bool) or not isinstance(answer, int):
            return False, "答案下标不是整数"
        if answer < 0 or answer >= len(choices):
            return False, "答案下标越界"
        correct_text = choices[answer]
        hits = [index for index, choice in enumerate(choices) if choice == correct_text]
        if hits != [answer]:
            return False, "检查题的正确选项不唯一"
    return True, ""


def self_check(lesson: dict) -> bool:
    try:
        ok, _reason = inspect_lesson(lesson)
    except Exception:
        return False
    return ok
