"""路由、内存中的课程、以及可选的静态页。"""

from __future__ import annotations

import asyncio
import time
from collections import OrderedDict
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException
from starlette.formparsers import FormParserError, MultiPartException

import skill
import vision

MAX_IMAGE_BYTES = 8 * 1024 * 1024
FORM_OVERHEAD = 64 * 1024
MAX_LESSONS = 64
LESSON_TTL_SECONDS = 6 * 60 * 60
IMAGE_ERROR = "请上传 8MB 以内的 png、jpeg 或 webp。"
CHECK_ERROR = "请答完三道题再提交。"
MISSING_LESSON = "这节课已经不在了，请重新打开页面。"
SELF_CHECK_ERROR = "这节课没有通过数学自检，没有生成。"
ASKED = "这张图是在讲正弦型函数 y = A sin(ωx + φ) 吗？"
DECLINED = "第一版只生成正弦型函数 y = A sin(ωx + φ)。"
QUADRATIC_ASKED = "这张图是在讲二次函数 y = a(x − h)² + k 吗？"
QUADRATIC_DECLINED = "这次不生成二次函数 y = a(x − h)² + k。"
LOGARITHM_ASKED = "这张图是在讲对数函数 y = logₐ(x) 吗？"
LOGARITHM_DECLINED = "这次不生成对数函数 y = logₐ(x)。"
EXPONENTIAL_ASKED = "这张图是在讲指数函数 y = aˣ 吗？"
EXPONENTIAL_DECLINED = "这次不生成指数函数 y = aˣ。"
TRIG_ASKED = "这张图是在讲三角函数 sin θ、cos θ、tan θ 吗？"
TRIG_DECLINED = "这次不生成三角函数 sin θ、cos θ、tan θ。"
ASK_TEXT = {
    "sinusoid": ASKED,
    "quadratic": QUADRATIC_ASKED,
    "logarithm": LOGARITHM_ASKED,
    "exponential": EXPONENTIAL_ASKED,
    "trig": TRIG_ASKED,
}
DECLINE_TEXT = {
    "sinusoid": DECLINED,
    "quadratic": QUADRATIC_DECLINED,
    "logarithm": LOGARITHM_DECLINED,
    "exponential": EXPONENTIAL_DECLINED,
    "trig": TRIG_DECLINED,
}
CONFIRM_CONCEPTS = ("sinusoid", "quadratic", "logarithm", "exponential", "trig")

ALLOWED_CONTENT_TYPES = {"image/png", "image/jpeg", "image/jpg", "image/webp"}
ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}

app = FastAPI()
LESSONS: OrderedDict[str, tuple[float, dict]] = OrderedDict()


def _image_type_ok(filename: str | None, content_type: str | None) -> bool:
    media = (content_type or "").split(";", 1)[0].strip().lower()
    if media in ALLOWED_CONTENT_TYPES:
        return True
    name = filename or ""
    suffix = ""
    if "." in name:
        suffix = "." + name.rsplit(".", 1)[-1].lower()
    return suffix in ALLOWED_EXTENSIONS


def validate_image_upload(filename: str | None, content_type: str | None, size: int):
    """合法返回 None，否则返回错误文案。"""
    if size <= 0 or size > MAX_IMAGE_BYTES or not _image_type_ok(filename, content_type):
        return IMAGE_ERROR
    return None


def content_length_error(header: str | None) -> str | None:
    """表单整体过大时，在解析正文之前拒绝。没有这个头则交给后续的分块上限。"""
    if header is None or not header.strip():
        return None
    try:
        length = int(header)
    except ValueError:
        return IMAGE_ERROR
    if length < 0 or length > MAX_IMAGE_BYTES + FORM_OVERHEAD:
        return IMAGE_ERROR
    return None


def _magic_ok(data: bytes) -> bool:
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return True
    if data.startswith(b"\xff\xd8\xff"):
        return True
    return len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP"


def _is_upload(value) -> bool:
    return value is not None and hasattr(value, "read") and hasattr(value, "filename")


def _clean_confirm(value):
    if not isinstance(value, str):
        return None
    text = value.strip()
    return text or None


def _purge(now: float) -> None:
    expired = [key for key, (saved, _lesson) in LESSONS.items() if now - saved > LESSON_TTL_SECONDS]
    for key in expired:
        del LESSONS[key]


def _remember(lesson: dict) -> dict:
    now = time.monotonic()
    _purge(now)
    LESSONS[lesson["id"]] = (now, lesson)
    LESSONS.move_to_end(lesson["id"])
    while len(LESSONS) > MAX_LESSONS:
        LESSONS.popitem(last=False)
    return lesson


def _recall(lesson_id: str) -> dict | None:
    item = LESSONS.get(lesson_id)
    if item is None:
        return None
    saved, lesson = item
    now = time.monotonic()
    if now - saved > LESSON_TTL_SECONDS:
        LESSONS.pop(lesson_id, None)
        return None
    LESSONS.move_to_end(lesson_id)
    LESSONS[lesson_id] = (now, lesson)
    return lesson


def _checked(lesson):
    return _remember(lesson)


def _confirmed_without_image(concept: str):
    if concept == "quadratic":
        return skill.generate_quadratic_confirmed_lesson()
    if concept == "logarithm":
        return skill.generate_logarithm_confirmed_lesson()
    if concept == "exponential":
        return skill.generate_exponential_confirmed_lesson()
    if concept == "trig":
        return skill.generate_trig_confirmed_lesson()
    return skill.generate_confirmed_lesson()


def _concept_of(value) -> str:
    if isinstance(value, str) and value.strip() in ("quadratic", "logarithm", "exponential", "trig"):
        return value.strip()
    return "sinusoid"


def _reject_body(concept: str = "sinusoid") -> dict:
    return {
        "id": None,
        "recognition": {
            "confident": False,
            "asked": None,
            "declined": DECLINE_TEXT.get(concept, DECLINED),
        },
    }


def _ask_body(concept: str = "sinusoid") -> dict:
    return {
        "id": None,
        "recognition": {
            "confident": False,
            "asked": ASK_TEXT.get(concept, ASKED),
            "readFailed": False,
            "choices": ["是，按这个知识点生成", "不是，先不生成"],
        },
    }


def _read_failed_body(recognition: dict) -> dict:
    reason = recognition.get("reason") if isinstance(recognition, dict) else ""
    if not isinstance(reason, str):
        reason = ""
    return {
        "id": None,
        "recognition": {
            "confident": False,
            "asked": None,
            "readFailed": True,
            "reason": vision.failure_text(reason),
        },
    }


def _answers_ok(answers) -> bool:
    if not isinstance(answers, list) or len(answers) != 3:
        return False
    for item in answers:
        if isinstance(item, bool) or not isinstance(item, int):
            return False
    return True


@app.get("/api/health")
def health():
    return {"ok": True, "vision": vision.status()}


@app.get("/api/sample")
def sample(concept: str | None = None):
    builders = {
        "quadratic": skill.generate_quadratic_default_lesson,
        "logarithm": skill.generate_logarithm_default_lesson,
        "exponential": skill.generate_exponential_default_lesson,
        "trig": skill.generate_trig_default_lesson,
    }
    try:
        lesson = builders.get(_concept_of(concept), skill.generate_default_lesson)()
    except skill.LessonCheckError:
        return JSONResponse(status_code=422, content={"error": SELF_CHECK_ERROR})
    return _checked(lesson)


@app.post("/api/lessons")
async def create_lesson(request: Request):
    content_type = request.headers.get("content-type", "")
    confirm = None
    concept = "sinusoid"
    image_bytes = None
    if "multipart/form-data" in content_type or "application/x-www-form-urlencoded" in content_type:
        too_big = content_length_error(request.headers.get("content-length"))
        if too_big:
            return JSONResponse(status_code=400, content={"error": too_big})
        try:
            form = await request.form(
                max_files=2,
                max_fields=8,
                max_part_size=MAX_IMAGE_BYTES,
            )
        except (MultiPartException, FormParserError, HTTPException):
            return JSONResponse(status_code=400, content={"error": IMAGE_ERROR})
        confirm = _clean_confirm(form.get("confirm"))
        concept = _concept_of(form.get("concept"))
        upload = form.get("image")
        if _is_upload(upload):
            known_size = upload.size if isinstance(upload.size, int) else None
            if known_size is not None and validate_image_upload(
                upload.filename, getattr(upload, "content_type", None), known_size
            ):
                return JSONResponse(status_code=400, content={"error": IMAGE_ERROR})
            data = await upload.read(MAX_IMAGE_BYTES + 1)
            if not upload.filename and not data:
                image_bytes = None
            else:
                error = validate_image_upload(
                    upload.filename,
                    getattr(upload, "content_type", None),
                    len(data),
                )
                if error or not _magic_ok(data):
                    return JSONResponse(status_code=400, content={"error": IMAGE_ERROR})
                image_bytes = data
    try:
        if confirm == "reject":
            return _reject_body(concept)
        if confirm in CONFIRM_CONCEPTS and image_bytes is None:
            return _checked(_confirmed_without_image(confirm))
        if image_bytes is not None:
            recognition = await asyncio.to_thread(skill.step1_read, image_bytes)
            if recognition.get("readFailed"):
                return _read_failed_body(recognition)
            if confirm in CONFIRM_CONCEPTS:
                return _checked(skill.lesson_from_recognition_for(confirm, recognition))
            if not skill.recognition_matches(concept, recognition):
                return _ask_body(concept)
            return _checked(skill.lesson_from_recognition_for(concept, recognition))
        if concept == "quadratic":
            return _checked(skill.generate_quadratic_default_lesson())
        if concept == "logarithm":
            return _checked(skill.generate_logarithm_default_lesson())
        if concept == "exponential":
            return _checked(skill.generate_exponential_default_lesson())
        if concept == "trig":
            return _checked(skill.generate_trig_default_lesson())
        return _checked(skill.generate_default_lesson())
    except skill.LessonCheckError:
        return JSONResponse(status_code=422, content={"error": SELF_CHECK_ERROR})


@app.post("/api/lessons/check")
async def check_lesson(request: Request):
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"error": CHECK_ERROR})
    if not isinstance(body, dict) or not _answers_ok(body.get("answers")):
        return JSONResponse(status_code=400, content={"error": CHECK_ERROR})
    lesson_id = body.get("lessonId")
    lesson = _recall(lesson_id) if isinstance(lesson_id, str) else None
    if lesson is None:
        return JSONResponse(status_code=404, content={"error": MISSING_LESSON})
    answers = body["answers"]
    items = []
    correct = 0
    for check, given in zip(lesson["checks"], answers):
        ok = given == check["answer"]
        if ok:
            correct += 1
        items.append({"id": check["id"], "ok": ok, "explain": check["explain"]})
    return {"correct": correct, "total": 3, "items": items}


_web = Path(__file__).resolve().parent.parent / "web"
if _web.is_dir():
    app.mount("/", StaticFiles(directory=_web, html=True), name="web")
