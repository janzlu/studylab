"""指数函数：只讲 y = aˣ，不和对数函数混在一节。"""

import sys
from io import BytesIO
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))

import app
import exponential
import skill
import vision


@pytest.fixture
def client():
    app.LESSONS.clear()
    with TestClient(app.app) as test_client:
        yield test_client
    app.LESSONS.clear()


def test_default_base_two_increases_and_passes_zero_one():
    lesson = skill.generate_exponential_default_lesson()
    assert lesson["id"] == "exponential-sample"
    assert lesson["conceptFamily"] == "exponential"
    assert lesson["animation"]["type"] == "exponential"
    assert lesson["animation"]["params"][0]["value"] == 2
    mono = lesson["beats"][1]["narration"]
    assert "递增" in mono
    assert "递减" not in mono
    point = lesson["beats"][2]["narration"]
    assert "(0, 1)" in point
    assert "(1, 0)" not in point
    reciprocal = lesson["beats"][3]["narration"]
    assert "y 轴" in reciprocal
    assert "x 轴" not in reciprocal
    assert "y = x" not in reciprocal
    assert "log" not in "".join(beat["narration"] for beat in lesson["beats"])
    assert [item["answer"] for item in lesson["checks"]] == [1, 1, 1]
    assert lesson["checks"][1]["choices"][1] == "(0, 1)"
    assert lesson["checks"][2]["choices"][1] == "y 轴"


def test_base_below_one_decreases():
    lesson = exponential.build_lesson(0.5, "exponential-test", None)
    mono = lesson["beats"][1]["narration"]
    assert "递减" in mono
    assert "递增" not in mono
    assert "改为 2" in lesson["checks"][0]["prompt"]
    assert lesson["checks"][0]["answer"] == 0


def test_tampered_base_fails_self_check():
    lesson = exponential.build_lesson(2, "exponential-bad-text", None)
    lesson["beats"][1]["narration"] = lesson["beats"][1]["narration"].replace("当前 a = 2", "当前 a = 99")
    ok, _reason = exponential.inspect_lesson(lesson)
    assert ok is False


def test_wrong_exponential_answer_is_marked_wrong(client):
    lesson = client.get("/api/sample?concept=exponential").json()
    response = client.post(
        "/api/lessons/check",
        json={"lessonId": lesson["id"], "answers": [0, 0, 0]},
    )
    body = response.json()
    assert body["correct"] == 0
    assert "(0, 1)" in body["items"][1]["explain"]
    assert "y 轴" in body["items"][2]["explain"]


def test_exponential_self_check_failure_returns_422(monkeypatch, client):
    calls = {"n": 0}

    def bad(*_args, **_kwargs):
        calls["n"] += 1
        return {"id": "exponential-bad", "beats": [], "checks": [], "animation": {"type": "exponential", "params": []}}

    monkeypatch.setattr(skill, "generate_exponential_lesson", bad)
    with pytest.raises(skill.LessonCheckError):
        skill.assemble_exponential_lesson(2, "exponential-bad", None)
    assert calls["n"] == 2
    response = client.post("/api/lessons", data={"concept": "exponential"})
    assert response.status_code == 422
    assert "animation" not in response.json()


def test_exponential_image_asks_and_confirm_uses_base_two(monkeypatch, client):
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
        data={"concept": "exponential"},
    )
    body = asked.json()
    assert "animation" not in body
    assert "指数函数" in body["recognition"]["asked"]
    assert "对数函数" not in body["recognition"]["asked"]
    confirmed = client.post("/api/lessons", data={"confirm": "exponential", "concept": "exponential"})
    lesson = confirmed.json()
    assert lesson["animation"]["params"][0]["value"] == 2
    assert "这版还不能从图片读出参数" in lesson["parameterNote"]


def test_exponential_reading_uses_the_base(monkeypatch, client):
    monkeypatch.setattr(
        vision,
        "complete",
        lambda _image: '{"concept":"exponential","isSinusoid":"no","base":3,"evidence":"y=3^x"}',
    )
    image = BytesIO()
    Image.new("RGB", (8, 8), "white").save(image, format="PNG")
    image.seek(0)
    response = client.post(
        "/api/lessons",
        files={"image": ("page.png", image, "image/png")},
        data={"concept": "exponential"},
    )
    body = response.json()
    assert body["animation"]["type"] == "exponential"
    assert body["animation"]["params"][0]["value"] == 3
    assert "当前 a = 3" in body["beats"][1]["narration"]
    assert "(0, 1)" in body["beats"][2]["narration"]


def test_logarithm_reading_on_exponential_tab_asks(monkeypatch, client):
    monkeypatch.setattr(
        vision,
        "complete",
        lambda _image: '{"concept":"logarithm","isSinusoid":"no","base":2,"evidence":"y=log"}',
    )
    image = BytesIO()
    Image.new("RGB", (8, 8), "white").save(image, format="PNG")
    image.seek(0)
    response = client.post(
        "/api/lessons",
        files={"image": ("page.png", image, "image/png")},
        data={"concept": "exponential"},
    )
    body = response.json()
    assert "animation" not in body
    assert "指数函数 y = aˣ" in body["recognition"]["asked"]


def test_exponential_reject_does_not_animate(client):
    response = client.post("/api/lessons", data={"confirm": "reject", "concept": "exponential"})
    body = response.json()
    assert "animation" not in body
    assert "指数函数" in body["recognition"]["declined"]
    assert "正弦" not in body["recognition"]["declined"]
