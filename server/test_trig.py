"""三角函数定义：只讲单位圆上的 sin、cos、tan，不讲正弦型函数。"""

import math
import sys
from io import BytesIO
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))

import app
import skill
import trig
import vision


@pytest.fixture
def client():
    app.LESSONS.clear()
    with TestClient(app.app) as test_client:
        yield test_client
    app.LESSONS.clear()


def test_default_theta_has_positive_sine():
    lesson = skill.generate_trig_default_lesson()
    assert lesson["id"] == "trig-sample"
    assert lesson["conceptFamily"] == "trig"
    assert lesson["animation"]["type"] == "trig"
    assert lesson["animation"]["params"][0]["value"] == pytest.approx(1.05)
    joined = "".join(beat["narration"] for beat in lesson["beats"])
    assert "当前 θ = 1.05" in joined
    assert "sin²θ + cos²θ = 1" in joined
    assert "正弦型" not in joined
    assert "ω" not in joined
    assert [item["answer"] for item in lesson["checks"]] == [1, 1, 0]
    assert lesson["checks"][1]["choices"][1] == "横坐标"
    assert lesson["checks"][2]["choices"][0] == "正"


def test_negative_sine_and_zero_and_undefined_tangent():
    negative = trig.build_lesson(4.71, "trig-neg", None)
    assert negative["checks"][2]["answer"] == 1
    assert negative["checks"][2]["choices"][1] == "负"
    zero = trig.build_lesson(0, "trig-zero", None)
    assert "当前 sin θ = 0" in zero["beats"][1]["narration"]
    assert zero["checks"][2]["answer"] == 2
    undefined = trig.build_lesson(math.pi / 2, "trig-tan", None)
    assert "tan θ 没有定义" in undefined["beats"][3]["narration"]


def test_degrees_convert_and_explicit_radians_do_not():
    theta, note = trig.resolve_params(60)
    assert "60" in note
    assert theta == pytest.approx(math.pi / 3, abs=1e-6)
    marked, marked_note = trig.resolve_params(30, "deg")
    assert "30" in marked_note
    assert marked == pytest.approx(math.pi / 6, abs=1e-6)
    kept, kept_note = trig.resolve_params(7, "rad")
    assert kept == pytest.approx(6.28)
    assert "角度" not in (kept_note or "")
    assert "夹到" in kept_note


def test_tampered_sine_fails_self_check():
    lesson = trig.build_lesson(1.05, "trig-bad-text", None)
    lesson["beats"][1]["narration"] = lesson["beats"][1]["narration"].replace("当前 sin θ", "当前错 θ")
    ok, _reason = trig.inspect_lesson(lesson)
    assert ok is False


def test_wrong_trig_answer_is_marked_wrong(client):
    lesson = client.get("/api/sample?concept=trig").json()
    response = client.post(
        "/api/lessons/check",
        json={"lessonId": lesson["id"], "answers": [0, 0, 2]},
    )
    body = response.json()
    assert body["correct"] == 0
    assert "1" in body["items"][0]["explain"]
    assert "横坐标" in body["items"][1]["explain"]


def test_trig_self_check_failure_returns_422(monkeypatch, client):
    calls = {"n": 0}

    def bad(*_args, **_kwargs):
        calls["n"] += 1
        return {"id": "trig-bad", "beats": [], "checks": [], "animation": {"type": "trig", "params": []}}

    monkeypatch.setattr(skill, "generate_trig_lesson", bad)
    with pytest.raises(skill.LessonCheckError):
        skill.assemble_trig_lesson(1.05, "trig-bad", None)
    assert calls["n"] == 2
    response = client.post("/api/lessons", data={"concept": "trig"})
    assert response.status_code == 422
    assert "animation" not in response.json()


def test_trig_image_asks_and_confirm_uses_default(monkeypatch, client):
    monkeypatch.setattr(
        vision,
        "complete",
        lambda _image: '{"concept":"unknown","isSinusoid":"unknown","evidence":""}',
    )
    image = BytesIO()
    Image.new("RGB", (8, 8), "white").save(image, format="PNG")
    image.seek(0)
    asked = client.post(
        "/api/lessons",
        files={"image": ("page.png", image, "image/png")},
        data={"concept": "trig"},
    )
    body = asked.json()
    assert "animation" not in body
    assert "三角函数" in body["recognition"]["asked"]
    assert "正弦型" not in body["recognition"]["asked"]
    confirmed = client.post("/api/lessons", data={"confirm": "trig", "concept": "trig"})
    lesson = confirmed.json()
    assert lesson["animation"]["params"][0]["value"] == pytest.approx(1.05)
    assert "图上未标出角" in lesson["parameterNote"]


def test_trig_reading_uses_degrees(monkeypatch, client):
    monkeypatch.setattr(
        vision,
        "complete",
        lambda _image: '{"concept":"trig","isSinusoid":"no","theta":60,"thetaUnit":"deg","evidence":"60°"}',
    )
    image = BytesIO()
    Image.new("RGB", (8, 8), "white").save(image, format="PNG")
    image.seek(0)
    response = client.post(
        "/api/lessons",
        files={"image": ("page.png", image, "image/png")},
        data={"concept": "trig"},
    )
    body = response.json()
    assert body["animation"]["type"] == "trig"
    assert body["animation"]["params"][0]["value"] == pytest.approx(math.pi / 3, abs=1e-4)
    assert "60" in body["parameterNote"]


def test_sinusoid_reading_on_trig_tab_asks(monkeypatch, client):
    monkeypatch.setattr(
        vision,
        "complete",
        lambda _image: '{"concept":"sinusoid","isSinusoid":"yes","A":1,"omega":1,"phi":0,"evidence":"y=sin"}',
    )
    image = BytesIO()
    Image.new("RGB", (8, 8), "white").save(image, format="PNG")
    image.seek(0)
    response = client.post(
        "/api/lessons",
        files={"image": ("page.png", image, "image/png")},
        data={"concept": "trig"},
    )
    body = response.json()
    assert "animation" not in body
    assert "三角函数" in body["recognition"]["asked"]


def test_trig_reject_does_not_animate(client):
    response = client.post("/api/lessons", data={"confirm": "reject", "concept": "trig"})
    body = response.json()
    assert "animation" not in body
    assert "三角函数" in body["recognition"]["declined"]
    assert "正弦型" not in body["recognition"]["declined"]
