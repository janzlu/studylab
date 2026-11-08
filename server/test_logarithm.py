"""对数函数：单调性翻面、定点、倒数对称、判分和自检。"""

import sys
from io import BytesIO
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))

import app
import logarithm
import skill
import vision


@pytest.fixture
def client():
    app.LESSONS.clear()
    with TestClient(app.app) as test_client:
        yield test_client
    app.LESSONS.clear()


def test_default_base_two_is_increasing_and_passes_one_zero():
    lesson = skill.generate_logarithm_default_lesson()
    assert lesson["id"] == "logarithm-sample"
    assert lesson["animation"]["type"] == "logarithm"
    assert lesson["animation"]["params"][0]["value"] == 2
    mono = lesson["beats"][1]["narration"]
    assert "递增" in mono
    assert "递减" not in mono
    assert "(1, 0)" in lesson["beats"][2]["narration"]
    assert "(0, 1)" not in lesson["beats"][2]["narration"]
    assert "x 轴" in lesson["beats"][3]["narration"]
    assert "y 轴" not in lesson["beats"][3]["narration"]
    assert [item["answer"] for item in lesson["checks"]] == [1, 1, 1]
    assert lesson["checks"][0]["choices"][1] == "递减"
    assert lesson["checks"][2]["choices"][1] == "x 轴"


def test_base_below_one_decreases_and_flips_back_to_increasing():
    lesson = logarithm.build_lesson(0.5, "logarithm-test", None)
    mono = lesson["beats"][1]["narration"]
    assert "递减" in mono
    assert "递增" not in mono
    assert "改为 2" in lesson["checks"][0]["prompt"]
    assert lesson["checks"][0]["answer"] == 0
    assert lesson["checks"][0]["choices"][0] == "递增"


def test_clamp_illegal_bases():
    base, note = logarithm.resolve_params(10)
    assert base == 4
    assert "10" in note and "a=4" in note
    base, note = logarithm.resolve_params(1)
    assert base == 2
    assert note
    base, note = logarithm.resolve_params(0.1)
    assert base == 0.25


def test_wrong_logarithm_answer_is_marked_wrong(client):
    lesson = client.get("/api/sample?concept=logarithm").json()
    response = client.post(
        "/api/lessons/check",
        json={"lessonId": lesson["id"], "answers": [0, 0, 0]},
    )
    body = response.json()
    assert body["correct"] == 0
    assert "递减" in body["items"][0]["explain"] or "递增" in body["items"][0]["explain"]
    assert "(1, 0)" in body["items"][1]["explain"]
    assert "x 轴" in body["items"][2]["explain"]


def test_logarithm_self_check_failure_returns_422(monkeypatch, client):
    calls = {"n": 0}

    def bad(*_args, **_kwargs):
        calls["n"] += 1
        return {"id": "logarithm-bad", "beats": [], "checks": [], "animation": {"type": "logarithm", "params": []}}

    monkeypatch.setattr(skill, "generate_logarithm_lesson", bad)
    with pytest.raises(skill.LessonCheckError):
        skill.assemble_logarithm_lesson(2, "logarithm-bad", None)
    assert calls["n"] == 2
    response = client.post("/api/lessons", data={"concept": "logarithm"})
    assert response.status_code == 422
    assert "animation" not in response.json()


def test_logarithm_image_asks_and_confirm_uses_base_two(monkeypatch, client):
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
        data={"concept": "logarithm"},
    )
    body = asked.json()
    assert "animation" not in body
    assert "对数函数" in body["recognition"]["asked"]
    confirmed = client.post("/api/lessons", data={"confirm": "logarithm", "concept": "logarithm"})
    lesson = confirmed.json()
    assert lesson["animation"]["params"][0]["value"] == 2
    assert "这版还不能从图片读出参数" in lesson["parameterNote"]


def test_logarithm_reject_does_not_animate(client):
    response = client.post("/api/lessons", data={"confirm": "reject", "concept": "logarithm"})
    body = response.json()
    assert "animation" not in body
    assert "对数函数" in body["recognition"]["declined"]
