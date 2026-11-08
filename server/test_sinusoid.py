import sys
from io import BytesIO
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import math

import pytest
from fastapi.testclient import TestClient
from PIL import Image

import app
import sinusoid
import skill
import vision


@pytest.fixture
def client():
    app.LESSONS.clear()
    with TestClient(app.app) as test_client:
        yield test_client
    app.LESSONS.clear()


def _beat(lesson, beat_id):
    for beat in lesson["beats"]:
        if beat["id"] == beat_id:
            return beat
    raise AssertionError(beat_id)


def _png_bytes() -> bytes:
    buffer = BytesIO()
    Image.new("RGB", (8, 8), (240, 236, 228)).save(buffer, format="PNG")
    return buffer.getvalue()


def test_default_period_is_two_pi():
    assert sinusoid.format_period(1) == "2π"
    assert sinusoid.period_value(1) == pytest.approx(2 * math.pi, abs=1e-9)
    lesson = sinusoid.build_lesson(1, 1, 0, "sinusoid-sample", None)
    assert "T = 2π" in _beat(lesson, "b2")["narration"]
    assert "T = 2π" in _beat(lesson, "b3")["narration"]
    ok, reason = sinusoid.inspect_lesson(lesson)
    assert ok, reason


def test_omega_two_period_is_pi_and_check_uses_half_pi():
    assert sinusoid.format_period(2) == "π"
    assert sinusoid.period_value(2) == pytest.approx(math.pi, abs=1e-9)
    lesson = sinusoid.build_lesson(1, 2, 0, "sinusoid-omega", None)
    assert "T = π" in _beat(lesson, "b3")["narration"]
    question = lesson["checks"][1]
    assert question["prompt"] == "ω 从 2 改为 4，周期是多少？"
    assert question["choices"] == ["π", "π/2", "π/4"]
    assert question["answer"] == 1
    assert question["choices"][question["answer"]] == "π/2"
    ok, reason = sinusoid.inspect_lesson(lesson)
    assert ok, reason


def test_positive_phase_shifts_left():
    lesson = sinusoid.build_lesson(1, 1, 1, "sinusoid-left", None)
    narration = _beat(lesson, "b4")["narration"]
    assert "向左" in narration
    assert "向右" not in narration
    ok, reason = sinusoid.inspect_lesson(lesson)
    assert ok, reason


def test_negative_phase_shifts_right_and_check_says_right():
    lesson = sinusoid.build_lesson(1, 1, -1, "sinusoid-right", None)
    narration = _beat(lesson, "b4")["narration"]
    assert "向右" in narration
    assert "向左" not in narration
    question = lesson["checks"][2]
    assert question["answer"] == 1
    assert question["choices"][question["answer"]] == "向右"
    ok, reason = sinusoid.inspect_lesson(lesson)
    assert ok, reason


def test_amplitude_does_not_change_period():
    assert list(sinusoid.period_value.__code__.co_varnames).count("amplitude") == 0
    low = sinusoid.build_lesson(0.5, 1, 0, "sinusoid-low", None)
    high = sinusoid.build_lesson(2.5, 1, 0, "sinusoid-high", None)
    assert "T = 2π" in _beat(low, "b3")["narration"]
    assert "T = 2π" in _beat(high, "b3")["narration"]
    assert low["checks"][0]["answer"] == 1
    assert high["checks"][0]["answer"] == 1
    assert low["checks"][0]["choices"][1] == "不变"
    doubled = sinusoid.build_lesson(2, 1, 0, "sinusoid-two", None)
    assert doubled["checks"][0]["answer"] == 1
    assert doubled["checks"][0]["prompt"].startswith("A 从 2 改为 1")


def test_wrong_answers_are_marked_wrong(client):
    sample = client.get("/api/sample")
    assert sample.status_code == 200
    lesson = sample.json()
    response = client.post(
        "/api/lessons/check",
        json={"lessonId": lesson["id"], "answers": [0, 0, 0]},
    )
    body = response.json()
    assert response.status_code == 200
    assert body["correct"] < 3
    assert body["total"] == 3
    assert len(body["items"]) == 3
    for item, check in zip(body["items"], lesson["checks"]):
        assert item["ok"] is False
        assert item["explain"]
        assert item["explain"] == check["explain"]


def test_right_answers_are_all_correct(client):
    lesson = client.get("/api/sample").json()
    expected = [item["answer"] for item in lesson["checks"]]
    assert expected == [1, 1, 1]
    response = client.post(
        "/api/lessons/check",
        json={"lessonId": lesson["id"], "answers": expected},
    )
    body = response.json()
    assert body["correct"] == 3
    assert body["total"] == 3
    assert [item["ok"] for item in body["items"]] == [True, True, True]


def test_self_check_failure_does_not_return_lesson(monkeypatch, client):
    calls = {"n": 0}

    def bad(*_args, **_kwargs):
        calls["n"] += 1
        return {
            "id": "sinusoid-bad",
            "beats": [],
            "checks": [],
            "animation": {"type": "other", "params": []},
        }

    monkeypatch.setattr(skill, "generate_lesson", bad)
    with pytest.raises(skill.LessonCheckError):
        result = skill.assemble_checked_lesson(1, 1, 0, "sinusoid-bad", None)
        assert result is None
    assert calls["n"] == 2

    response = client.post("/api/lessons")
    body = response.json()
    assert response.status_code == 422
    assert body == {"error": "这节课没有通过数学自检，没有生成。"}
    assert "animation" not in body
    assert app.LESSONS == {}


def test_post_without_image_returns_default_lesson(monkeypatch, client):
    def boom(_image_bytes):
        raise AssertionError("无图不应读图")

    monkeypatch.setattr(vision, "recognize", boom)
    response = client.post("/api/lessons")
    body = response.json()
    assert response.status_code == 200
    assert body["id"] == "sinusoid-sample"
    assert body["parameterNote"] is None
    assert body["animation"]["type"] == "sinusoid"
    values = [item["value"] for item in body["animation"]["params"]]
    assert values == [1, 1, 0]
    assert body["id"] in app.LESSONS


def test_png_without_confirm_asks_and_does_not_animate(monkeypatch, client):
    monkeypatch.setattr(
        vision,
        "complete",
        lambda _image: '{"concept":"unknown","isSinusoid":"unknown","evidence":""}',
    )
    response = client.post(
        "/api/lessons",
        files={"image": ("page.png", _png_bytes(), "image/png")},
    )
    body = response.json()
    assert response.status_code == 200
    assert "animation" not in body
    assert body["id"] is None
    assert body["recognition"]["asked"] == "这张图是在讲正弦型函数 y = A sin(ωx + φ) 吗？"
    assert body["recognition"]["confident"] is False
    assert app.LESSONS == {}


def test_confirm_without_image_uses_default_and_says_params_unread(client):
    response = client.post("/api/lessons", data={"confirm": "sinusoid"})
    body = response.json()
    assert response.status_code == 200
    assert body["animation"]["type"] == "sinusoid"
    assert "这版还不能从图片读出参数" in body["parameterNote"]
    assert "图上未标出参数，先按 A=1，ω=1，φ=0 讲这个知识点。" in body["parameterNote"]
    assert body["id"] in app.LESSONS


def test_confirm_with_unreadable_image_does_not_invent_a_lesson(monkeypatch, client):
    def boom(_image_bytes):
        raise RuntimeError("视觉接口没连上")

    monkeypatch.setattr(vision, "complete", boom)
    response = client.post(
        "/api/lessons",
        data={"confirm": "sinusoid"},
        files={"image": ("page.png", _png_bytes(), "image/png")},
    )
    body = response.json()
    assert response.status_code == 200
    assert "animation" not in body
    assert body["recognition"]["readFailed"] is True
    assert body["recognition"]["asked"] is None
    assert "不可用" in body["recognition"]["reason"]
    assert app.LESSONS == {}


def test_confirm_reject_does_not_animate(client):
    response = client.post(
        "/api/lessons",
        data={"confirm": "reject"},
        files={"image": ("page.png", _png_bytes(), "image/png")},
    )
    body = response.json()
    assert response.status_code == 200
    assert "animation" not in body
    assert body["recognition"]["declined"] == "第一版只生成正弦型函数 y = A sin(ωx + φ)。"
    assert app.LESSONS == {}


def test_bad_type_and_oversize_are_rejected(client):
    response = client.post(
        "/api/lessons",
        files={"image": ("notes.txt", b"not an image", "text/plain")},
    )
    assert response.status_code == 400
    assert response.json() == {"error": "请上传 8MB 以内的 png、jpeg 或 webp。"}
    assert (
        app.validate_image_upload("big.png", "image/png", 8 * 1024 * 1024 + 1)
        == "请上传 8MB 以内的 png、jpeg 或 webp。"
    )
    assert app.validate_image_upload("big.png", "image/png", 8 * 1024 * 1024) is None


def test_clamp_amplitude_nine_to_two_point_five():
    lesson = sinusoid.lesson_for_reading(9, 1, 0, "sinusoid-clamp")
    assert lesson["animation"]["params"][0]["value"] == 2.5
    assert "9" in lesson["parameterNote"]
    assert "2.5" in lesson["parameterNote"]
    ok, reason = sinusoid.inspect_lesson(lesson)
    assert ok, reason


def test_health(client):
    response = client.get("/api/health")
    body = response.json()
    assert response.status_code == 200
    assert body["ok"] is True
    assert set(body["vision"]) == {"enabled", "loopback", "remoteAllowed"}


def test_unknown_lesson_and_incomplete_answers(client):
    missing = client.post(
        "/api/lessons/check",
        json={"lessonId": "sinusoid-missing", "answers": [1, 1, 1]},
    )
    assert missing.status_code == 404
    assert missing.json() == {"error": "这节课已经不在了，请重新打开页面。"}
    incomplete = client.post(
        "/api/lessons/check",
        json={"lessonId": "sinusoid-sample", "answers": [1]},
    )
    assert incomplete.status_code == 400
    assert incomplete.json() == {"error": "请答完三道题再提交。"}
