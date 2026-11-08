"""读图只提供知识点和数字。讲解仍由模板生成，失败时不假装已识别。"""

import sys
from io import BytesIO
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))

import app
import quadratic
import sinusoid
import vision


@pytest.fixture
def client():
    app.LESSONS.clear()
    with TestClient(app.app) as test_client:
        yield test_client
    app.LESSONS.clear()


def _png() -> bytes:
    buffer = BytesIO()
    Image.new("RGB", (32, 32), (255, 255, 255)).save(buffer, format="PNG")
    return buffer.getvalue()


def _reading(**overrides) -> str:
    payload = {
        "concept": "sinusoid",
        "isSinusoid": "yes",
        "A": 1,
        "omega": 2,
        "phi": 0,
        "a": None,
        "h": None,
        "k": None,
        "b": None,
        "c": None,
        "base": None,
        "evidence": "y = sin(2x)",
    }
    payload.update(overrides)
    import json

    return json.dumps(payload)


def test_parse_accepts_fenced_json_and_pi_text():
    text = """<think>先看公式</think>
```json
{"concept":"sinusoid","isSinusoid":"yes","A":"2","omega":2,"phi":"π/2","evidence":"y=2sin(2x+π/2)"}
```
"""
    parsed = vision.parse_model_text(text)
    assert parsed["concept"] == "sinusoid"
    assert parsed["isSinusoid"] == "yes"
    assert parsed["A"] == 2
    assert parsed["omega"] == 2
    assert parsed["phi"] == pytest.approx(math_pi_over_two())
    assert parsed["readFailed"] is False
    assert "讲解" not in parsed["evidence"]


def math_pi_over_two():
    import math

    return math.pi / 2


def test_parse_rejects_prose_and_does_not_invent_yes():
    assert vision.parse_model_text("这是正弦型函数，A=2") is None
    assert vision.parse_model_text('{"concept":"quadratic","isSinusoid":"yes","a":1}')["isSinusoid"] == "no"


def test_partial_sinusoid_note_names_the_missing_parameters():
    _amplitude, _omega, _phi, note = sinusoid.resolve_params(2, None, None)
    assert note == "图上未标出 ω、φ，先按 ω=1，φ=0。"


def test_general_quadratic_becomes_vertex_form():
    amplitude, horizontal, vertical, note = quadratic.reading_params(1, None, None, -2, 1)
    assert amplitude == 1
    assert horizontal == 1
    assert vertical == 0
    assert note is None


def test_unreadable_bytes_do_not_call_the_model(monkeypatch):
    def boom(_image):
        raise AssertionError("坏图不应请求模型")

    monkeypatch.setattr(vision, "complete", boom)
    parsed = vision.recognize(b"not an image")
    assert parsed["isSinusoid"] == "unknown"
    assert parsed["readFailed"] is True


def test_model_failure_asks_instead_of_inventing_a_lesson(monkeypatch, client):
    def boom(_image):
        raise RuntimeError("down")

    monkeypatch.setattr(vision, "complete", boom)
    response = client.post(
        "/api/lessons",
        files={"image": ("page.png", _png(), "image/png")},
    )
    body = response.json()
    assert response.status_code == 200
    assert "animation" not in body
    assert body["recognition"]["asked"] is None
    assert body["recognition"]["readFailed"] is True
    assert "不可用" in body["recognition"]["reason"]
    assert app.LESSONS == {}


def test_recognized_omega_two_generates_recomputed_checks(monkeypatch, client):
    monkeypatch.setattr(vision, "complete", lambda _image: _reading())
    response = client.post(
        "/api/lessons",
        files={"image": ("page.png", _png(), "image/png")},
    )
    body = response.json()
    assert response.status_code == 200
    assert body["animation"]["type"] == "sinusoid"
    assert [item["value"] for item in body["animation"]["params"]] == [1, 2, 0]
    assert "ω 从 2 改为 4" in body["checks"][1]["prompt"]
    assert body["checks"][1]["choices"][body["checks"][1]["answer"]] == "π/2"
    assert "不能从图片读出参数" not in (body["parameterNote"] or "")
    assert "旁白" not in "".join(beat["narration"] for beat in body["beats"])


def test_other_concept_on_sinusoid_tab_asks(monkeypatch, client):
    monkeypatch.setattr(
        vision,
        "complete",
        lambda _image: _reading(concept="quadratic", isSinusoid="no", a=1, h=0, k=0, A=None, omega=None),
    )
    response = client.post(
        "/api/lessons",
        files={"image": ("page.png", _png(), "image/png")},
        data={"concept": "sinusoid"},
    )
    body = response.json()
    assert "animation" not in body
    assert "正弦型函数" in body["recognition"]["asked"]


def test_quadratic_reading_generates_that_lesson(monkeypatch, client):
    monkeypatch.setattr(
        vision,
        "complete",
        lambda _image: _reading(
            concept="quadratic",
            isSinusoid="no",
            A=None,
            omega=None,
            phi=None,
            a=1,
            b=-2,
            c=1,
        ),
    )
    response = client.post(
        "/api/lessons",
        files={"image": ("page.png", _png(), "image/png")},
        data={"concept": "quadratic"},
    )
    body = response.json()
    assert body["animation"]["type"] == "quadratic"
    values = {item["key"]: item["value"] for item in body["animation"]["params"]}
    assert values == {"a": 1, "h": 1, "k": 0}


def test_confirm_uses_numbers_read_from_the_image(monkeypatch, client):
    monkeypatch.setattr(vision, "complete", lambda _image: _reading(A=2, omega=1, phi=0))
    response = client.post(
        "/api/lessons",
        data={"confirm": "sinusoid", "concept": "sinusoid"},
        files={"image": ("page.png", _png(), "image/png")},
    )
    body = response.json()
    assert [item["value"] for item in body["animation"]["params"]] == [2, 1, 0]
    assert "不能从图片读出参数" not in (body["parameterNote"] or "")
