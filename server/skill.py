"""四步管线：读图、列讲解、生成、自检。

大模型只进入第 1 步，而且只提供知识点和数字。旁白与检查题仍由模板写。
"""

from __future__ import annotations

from uuid import uuid4

import exponential
import logarithm
import trig
import quadratic
import sinusoid
import vision

CONFIRMED_NOTE = (
    "这版还不能从图片读出参数。图上未标出参数，先按 A=1，ω=1，φ=0 讲这个知识点。"
)
QUADRATIC_CONFIRMED_NOTE = (
    "这版还不能从图片读出参数。图上未标出参数，先按 a=1，h=0，k=0 讲这个知识点。"
)
SAMPLE_ID = "sinusoid-sample"
QUADRATIC_SAMPLE_ID = "quadratic-sample"
LOGARITHM_SAMPLE_ID = "logarithm-sample"
LOGARITHM_CONFIRMED_NOTE = (
    "这版还不能从图片读出参数。图上未标出参数，先按 a=2 讲这个知识点。"
)
EXPONENTIAL_SAMPLE_ID = "exponential-sample"
TRIG_SAMPLE_ID = "trig-sample"
EXPONENTIAL_CONFIRMED_NOTE = LOGARITHM_CONFIRMED_NOTE
TRIG_CONFIRMED_NOTE = (
    "这版还不能从图片读出参数。图上未标出角，先按 θ=1.05 讲这个知识点。"
)


class LessonCheckError(Exception):
    """连续两次自检失败。调用方不得把课程对象返回出去。"""


def new_lesson_id() -> str:
    return "sinusoid-" + uuid4().hex[:8]


def step1_read(image_bytes: bytes, model=None) -> dict:
    """第 1 步读图。model 只保留接口形状，调用发生在 vision 里。"""
    del model
    return vision.recognize(image_bytes)


def recognition_matches(concept: str, recognition: dict) -> bool:
    """图上的知识点和当前选择一致时，才直接生成。"""
    if not isinstance(recognition, dict) or recognition.get("readFailed"):
        return False
    seen = recognition.get("concept")
    if concept == "sinusoid":
        if seen in {"quadratic", "logarithm", "exponential", "trig"}:
            return False
        return recognition.get("isSinusoid") == "yes"
    return seen == concept


def step2_plan(raw_a, raw_omega, raw_phi, parameter_note=None, use_resolver: bool = True) -> dict:
    """第 2 步列讲解：确定采用的参数和说明，不写旁白以外的正文。"""
    if use_resolver:
        amplitude, omega, phi, note = sinusoid.resolve_params(raw_a, raw_omega, raw_phi)
    else:
        amplitude, omega, phi, note = raw_a, raw_omega, raw_phi, parameter_note
    return {
        "A": amplitude,
        "omega": omega,
        "phi": phi,
        "parameterNote": note,
    }


def generate_lesson(amplitude, omega, phi, lesson_id, parameter_note) -> dict:
    """第 3 步生成。测试可以替换这个函数。"""
    return sinusoid.build_lesson(amplitude, omega, phi, lesson_id, parameter_note)


def step4_self_check(lesson: dict) -> bool:
    return sinusoid.self_check(lesson)


def assemble_checked_lesson(amplitude, omega, phi, lesson_id, parameter_note) -> dict:
    """生成并自检。失败就用同一套参数再生成一次，仍失败则抛错，不返回课。"""
    last_reason = "未生成"
    for _attempt in range(2):
        lesson = generate_lesson(amplitude, omega, phi, lesson_id, parameter_note)
        ok, reason = sinusoid.inspect_lesson(lesson) if isinstance(lesson, dict) else (False, "课程不是对象")
        if ok and step4_self_check(lesson):
            return lesson
        last_reason = reason
    raise LessonCheckError(f"这节课没有通过数学自检，没有生成。{last_reason}")


def generate_default_lesson() -> dict:
    """无图：不读图，从第 2 步走到第 4 步，参数用默认值。"""
    plan = step2_plan(1, 1, 0, parameter_note=None, use_resolver=False)
    return assemble_checked_lesson(
        plan["A"], plan["omega"], plan["phi"], SAMPLE_ID, plan["parameterNote"]
    )


def generate_confirmed_lesson() -> dict:
    """用户确认按正弦型函数讲。当前读不出图上的数字，用默认参数。"""
    plan = step2_plan(1, 1, 0, parameter_note=CONFIRMED_NOTE, use_resolver=False)
    return assemble_checked_lesson(
        plan["A"],
        plan["omega"],
        plan["phi"],
        new_lesson_id(),
        plan["parameterNote"],
    )


def generate_quadratic_lesson(amplitude, horizontal, vertical, lesson_id, parameter_note) -> dict:
    """二次函数的第 3 步。测试可以替换这个函数。"""
    return quadratic.build_lesson(amplitude, horizontal, vertical, lesson_id, parameter_note)


def assemble_quadratic_lesson(amplitude, horizontal, vertical, lesson_id, parameter_note) -> dict:
    last_reason = "未生成"
    for _attempt in range(2):
        lesson = generate_quadratic_lesson(
            amplitude, horizontal, vertical, lesson_id, parameter_note
        )
        ok, reason = (
            quadratic.inspect_lesson(lesson) if isinstance(lesson, dict) else (False, "课程不是对象")
        )
        if ok and quadratic.self_check(lesson):
            return lesson
        last_reason = reason
    raise LessonCheckError(f"这节课没有通过数学自检，没有生成。{last_reason}")


def generate_quadratic_default_lesson() -> dict:
    return assemble_quadratic_lesson(1, 0, 0, QUADRATIC_SAMPLE_ID, None)


def generate_quadratic_confirmed_lesson() -> dict:
    return assemble_quadratic_lesson(
        1,
        0,
        0,
        "quadratic-" + uuid4().hex[:8],
        QUADRATIC_CONFIRMED_NOTE,
    )


def generate_logarithm_lesson(base, lesson_id, parameter_note) -> dict:
    """对数函数的第 3 步。测试可以替换这个函数。"""
    return logarithm.build_lesson(base, lesson_id, parameter_note)


def assemble_logarithm_lesson(base, lesson_id, parameter_note) -> dict:
    last_reason = "未生成"
    for _attempt in range(2):
        lesson = generate_logarithm_lesson(base, lesson_id, parameter_note)
        ok, reason = (
            logarithm.inspect_lesson(lesson) if isinstance(lesson, dict) else (False, "课程不是对象")
        )
        if ok and logarithm.self_check(lesson):
            return lesson
        last_reason = reason
    raise LessonCheckError(f"这节课没有通过数学自检，没有生成。{last_reason}")


def generate_logarithm_default_lesson() -> dict:
    return assemble_logarithm_lesson(2, LOGARITHM_SAMPLE_ID, None)


def generate_logarithm_confirmed_lesson() -> dict:
    return assemble_logarithm_lesson(
        2,
        "logarithm-" + uuid4().hex[:8],
        LOGARITHM_CONFIRMED_NOTE,
    )


def lesson_from_recognition(recognition: dict) -> dict:
    """第 1 步已经确认是正弦型函数时，走第 2 步到第 4 步。"""
    plan = step2_plan(
        recognition.get("A"),
        recognition.get("omega"),
        recognition.get("phi"),
    )
    return assemble_checked_lesson(
        plan["A"],
        plan["omega"],
        plan["phi"],
        new_lesson_id(),
        plan["parameterNote"],
    )


def lesson_from_quadratic_recognition(recognition: dict) -> dict:
    amplitude, horizontal, vertical, note = quadratic.reading_params(
        recognition.get("a"),
        recognition.get("h"),
        recognition.get("k"),
        recognition.get("b"),
        recognition.get("c"),
    )
    return assemble_quadratic_lesson(
        amplitude,
        horizontal,
        vertical,
        "quadratic-" + uuid4().hex[:8],
        note,
    )


def lesson_from_logarithm_recognition(recognition: dict) -> dict:
    base, note = logarithm.resolve_params(recognition.get("base"))
    return assemble_logarithm_lesson(
        base,
        "logarithm-" + uuid4().hex[:8],
        note,
    )


def generate_exponential_lesson(base, lesson_id, parameter_note) -> dict:
    """指数函数的第 3 步。测试可以替换这个函数。"""
    return exponential.build_lesson(base, lesson_id, parameter_note)


def assemble_exponential_lesson(base, lesson_id, parameter_note) -> dict:
    last_reason = "未生成"
    for _attempt in range(2):
        lesson = generate_exponential_lesson(base, lesson_id, parameter_note)
        ok, reason = (
            exponential.inspect_lesson(lesson) if isinstance(lesson, dict) else (False, "课程不是对象")
        )
        if ok and exponential.self_check(lesson):
            return lesson
        last_reason = reason
    raise LessonCheckError(f"这节课没有通过数学自检，没有生成。{last_reason}")


def generate_exponential_default_lesson() -> dict:
    return assemble_exponential_lesson(2, EXPONENTIAL_SAMPLE_ID, None)


def generate_exponential_confirmed_lesson() -> dict:
    return assemble_exponential_lesson(
        2,
        "exponential-" + uuid4().hex[:8],
        EXPONENTIAL_CONFIRMED_NOTE,
    )


def lesson_from_exponential_recognition(recognition: dict) -> dict:
    base, note = exponential.resolve_params(recognition.get("base"))
    return assemble_exponential_lesson(
        base,
        "exponential-" + uuid4().hex[:8],
        note,
    )


def generate_trig_lesson(theta, lesson_id, parameter_note) -> dict:
    """三角函数的第 3 步。测试可以替换这个函数。"""
    return trig.build_lesson(theta, lesson_id, parameter_note)


def assemble_trig_lesson(theta, lesson_id, parameter_note) -> dict:
    last_reason = "未生成"
    for _attempt in range(2):
        lesson = generate_trig_lesson(theta, lesson_id, parameter_note)
        ok, reason = trig.inspect_lesson(lesson) if isinstance(lesson, dict) else (False, "课程不是对象")
        if ok and trig.self_check(lesson):
            return lesson
        last_reason = reason
    raise LessonCheckError(f"这节课没有通过数学自检，没有生成。{last_reason}")


def generate_trig_default_lesson() -> dict:
    return assemble_trig_lesson(trig.THETA_DEFAULT, TRIG_SAMPLE_ID, None)


def generate_trig_confirmed_lesson() -> dict:
    return assemble_trig_lesson(
        trig.THETA_DEFAULT,
        "trig-" + uuid4().hex[:8],
        TRIG_CONFIRMED_NOTE,
    )


def lesson_from_trig_recognition(recognition: dict) -> dict:
    theta, note = trig.resolve_params(recognition.get("theta"), recognition.get("thetaUnit"))
    return assemble_trig_lesson(
        theta,
        "trig-" + uuid4().hex[:8],
        note,
    )


def lesson_from_recognition_for(concept: str, recognition: dict) -> dict:
    if concept == "quadratic":
        return lesson_from_quadratic_recognition(recognition)
    if concept == "logarithm":
        return lesson_from_logarithm_recognition(recognition)
    if concept == "exponential":
        return lesson_from_exponential_recognition(recognition)
    if concept == "trig":
        return lesson_from_trig_recognition(recognition)
    return lesson_from_recognition(recognition)
