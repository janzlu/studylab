"""二次函数：开口、对称轴方向、顶点高低、判分和自检。"""

import sys
from io import BytesIO
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))

import app
import quadratic
import skill
import vision


@pytest.fixture
def client():
    app.LESSONS.clear()
    with TestClient(app.app) as test_client:
        yield test_client
    app.LESSONS.clear()


def _lesson(amplitude=1, horizontal=0, vertical=0):
    return quadratic.build_lesson(amplitude, horizontal, vertical, "quadratic-test", None)


def test_default_opens_upward_with_vertex_at_origin():
    lesson = skill.generate_quadratic_default_lesson()
    assert lesson["id"] == "quadratic-sample"
    assert lesson["animation"]["type"] == "quadratic"
    values = {item["key"]: item["value"] for item in lesson["animation"]["params"]}
    assert values == {"a": 1, "h": 0, "k": 0}
    assert "开口向上" in lesson["beats"][1]["narration"]
    assert "向下" not in lesson["beats"][1]["narration"]
    assert "就是 y 轴" in lesson["beats"][2]["narration"]
    assert lesson["checks"][0]["answer"] == 1
    assert lesson["checks"][0]["choices"][1] == "变窄"
    assert lesson["checks"][1]["choices"][1] == "向右"
    assert lesson["checks"][2]["choices"][1] == "向上"


def test_larger_abs_a_narrows_and_smaller_widens():
    narrow = _lesson(1, 0, 0)
    assert "改为 2" in narrow["checks"][0]["prompt"]
    assert narrow["checks"][0]["answer"] == 1
    wide = _lesson(2, 0, 0)
    assert "改为 1" in wide["checks"][0]["prompt"]
    assert wide["checks"][0]["answer"] == 0
    assert wide["checks"][0]["choices"][0] == "变宽"


def test_negative_a_opens_down_and_keeps_sign_when_width_changes():
    lesson = _lesson(-1, 0, 0)
    narration = lesson["beats"][1]["narration"]
    assert "开口向下" in narration
    assert "向上" not in narration
    assert "改为 -2" in lesson["checks"][0]["prompt"]
    assert lesson["checks"][0]["answer"] == 1


def test_h_positive_moves_axis_right_and_negative_stays_left():
    right = _lesson(1, 0, 0)
    assert right["checks"][1]["answer"] == 1
    assert "向右" in right["checks"][1]["explain"]
    left = _lesson(1, -2, 0)
    narration = left["beats"][2]["narration"]
    assert "左侧" in narration
    assert "右" not in narration


def test_k_positive_moves_vertex_up_and_negative_moves_down():
    up = _lesson(1, 0, 0)
    assert up["checks"][2]["answer"] == 1
    down = _lesson(1, 0, -2)
    narration = down["beats"][3]["narration"]
    assert "向下" in narration
    assert "向上" not in narration
    assert down["checks"][2]["answer"] == 1
    assert "改为 2" in down["checks"][2]["prompt"]


def test_clamp_large_a_and_records_original():
    amplitude, horizontal, vertical, note = quadratic.resolve_params(9, 0, 0)
    assert amplitude == 2
    assert horizontal == 0
    assert vertical == 0
    assert "9" in note
    assert "a=2" in note


def test_wrong_quadratic_answer_is_marked_wrong(client):
    lesson = client.get("/api/sample?concept=quadratic").json()
    response = client.post(
        "/api/lessons/check",
        json={"lessonId": lesson["id"], "answers": [0, 0, 0]},
    )
    body = response.json()
    assert body["correct"] == 0
    assert body["items"][0]["ok"] is False
    assert "开口" in body["items"][0]["explain"]


def test_quadratic_self_check_failure_returns_422(monkeypatch, client):
    calls = {"n": 0}

    def bad(*_args, **_kwargs):
        calls["n"] += 1
        return {"id": "quadratic-bad", "beats": [], "checks": [], "animation": {"type": "quadratic", "params": []}}

    monkeypatch.setattr(skill, "generate_quadratic_lesson", bad)
    with pytest.raises(skill.LessonCheckError):
        skill.assemble_quadratic_lesson(1, 0, 0, "quadratic-bad", None)
    assert calls["n"] == 2
    response = client.post("/api/lessons", data={"concept": "quadratic"})
    assert response.status_code == 422
    assert "animation" not in response.json()


def test_quadratic_image_asks_and_confirm_notes_unread_params(monkeypatch, client):
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
        data={"concept": "quadratic"},
    )
    body = asked.json()
    assert asked.status_code == 200
    assert "animation" not in body
    assert "二次函数" in body["recognition"]["asked"]

    confirmed = client.post("/api/lessons", data={"confirm": "quadratic", "concept": "quadratic"})
    lesson = confirmed.json()
    assert lesson["animation"]["type"] == "quadratic"
    assert "这版还不能从图片读出参数" in lesson["parameterNote"]
    assert lesson["animation"]["params"][0]["value"] == 1


def test_quadratic_reject_does_not_animate(client):
    response = client.post("/api/lessons", data={"confirm": "reject", "concept": "quadratic"})
    body = response.json()
    assert "animation" not in body
    assert "二次函数" in body["recognition"]["declined"]
    assert "正弦" not in body["recognition"]["declined"]
