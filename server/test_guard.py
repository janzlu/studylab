"""P0 守门：正文数值、读图失败原因、上传边界、密钥与本机地址。"""

import json
import math
import subprocess
import sys
from io import BytesIO
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))

import app
import exponential
import logarithm
import quadratic
import sinusoid
import trig
import vision

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def client():
    app.LESSONS.clear()
    with TestClient(app.app) as test_client:
        yield test_client
    app.LESSONS.clear()


def _png() -> bytes:
    buffer = BytesIO()
    Image.new("RGB", (8, 8), "white").save(buffer, format="PNG")
    return buffer.getvalue()


def test_tampered_narration_numbers_fail_self_check():
    cases = []

    lesson = sinusoid.build_lesson(1, 1, 0, "s", None)
    lesson["beats"][1]["narration"] = lesson["beats"][1]["narration"].replace("当前 A = 1", "当前 A = 99")
    cases.append(sinusoid.inspect_lesson(lesson))

    lesson = sinusoid.build_lesson(1, 1, 0, "s", None)
    lesson["beats"][2]["narration"] = lesson["beats"][2]["narration"].replace("当前 ω = 1", "当前 ω = 99")
    cases.append(sinusoid.inspect_lesson(lesson))

    lesson = sinusoid.build_lesson(1, 1, 0, "s", None)
    lesson["beats"][1]["narration"] = lesson["beats"][1]["narration"].replace("T = 2π", "T = 2π/3")
    cases.append(sinusoid.inspect_lesson(lesson))

    lesson = quadratic.build_lesson(1, 0, 0, "q", None)
    lesson["beats"][0]["narration"] = lesson["beats"][0]["narration"].replace("(0, 0)", "(9, 9)")
    cases.append(quadratic.inspect_lesson(lesson))

    lesson = quadratic.build_lesson(1, 0, 0, "q", None)
    lesson["beats"][1]["narration"] = lesson["beats"][1]["narration"].replace("当前 a = 1", "当前 a = 99")
    cases.append(quadratic.inspect_lesson(lesson))

    lesson = quadratic.build_lesson(1, 0, 0, "q", None)
    lesson["beats"][2]["narration"] = lesson["beats"][2]["narration"].replace("x = 0", "x = 99")
    cases.append(quadratic.inspect_lesson(lesson))

    lesson = quadratic.build_lesson(1, 0, 0, "q", None)
    lesson["beats"][3]["narration"] = lesson["beats"][3]["narration"].replace("y = 0", "y = 99")
    cases.append(quadratic.inspect_lesson(lesson))

    lesson = logarithm.build_lesson(2, "g", None)
    lesson["beats"][1]["narration"] = lesson["beats"][1]["narration"].replace("当前 a = 2", "当前 a = 99")
    cases.append(logarithm.inspect_lesson(lesson))

    lesson = logarithm.build_lesson(2, "g", None)
    lesson["beats"][3]["narration"] = lesson["beats"][3]["narration"].replace("0.5", "9")
    cases.append(logarithm.inspect_lesson(lesson))

    lesson = logarithm.build_lesson(2, "g", None)
    lesson["beats"][0]["narration"] = lesson["beats"][0]["narration"].replace("x>0", "x>99")
    cases.append(logarithm.inspect_lesson(lesson))

    assert cases
    assert all(ok is False for ok, _reason in cases)


def test_slider_narration_matches_server_templates():
    cases = []
    for amplitude in (0.5, 1, 1.7, 2.5):
        for step in range(5, 31):
            omega = step / 10
            for phi in (-3.14, -1.57, 0, 1.57, 3.14):
                beats = sinusoid._beat_narration(amplitude, omega, phi)
                cases.append(
                    {
                        "family": "sinusoid",
                        "params": {"A": amplitude, "omega": omega, "phi": phi},
                        "beats": {beat["id"]: beat["narration"] for beat in beats},
                    }
                )
    for opening in (-2, -0.5, 0.5, 2):
        for horizontal in (-3, 0, 1.5):
            beats = quadratic.build_beats(opening, horizontal, 0)
            cases.append(
                {
                    "family": "quadratic",
                    "params": {"a": opening, "h": horizontal, "k": 0},
                    "beats": {beat["id"]: beat["narration"] for beat in beats},
                }
            )
    for base in (0.25, 0.5, 0.8, 1.25, 2, 3, 4):
        beats = logarithm.build_beats(base)
        cases.append(
            {
                "family": "logarithm",
                "params": {"base": base},
                "beats": {beat["id"]: beat["narration"] for beat in beats},
            }
        )
        beats = exponential.build_beats(base)
        cases.append(
            {
                "family": "exponential",
                "params": {"base": base},
                "beats": {beat["id"]: beat["narration"] for beat in beats},
            }
        )
    for theta in (0, 1.05, math.pi / 2, 3.14, 4.71, 6.28):
        beats = trig.build_beats(theta)
        cases.append(
            {
                "family": "trig",
                "params": {"theta": theta},
                "beats": {beat["id"]: beat["narration"] for beat in beats},
            }
        )
    script = """
const n = require(process.argv[1]);
let raw = "";
process.stdin.on("data", (chunk) => { raw += chunk; });
process.stdin.on("end", () => {
  const cases = JSON.parse(raw);
  for (const item of cases) {
    const got = n.narrations(item.family, item.params);
    for (const id of Object.keys(item.beats)) {
      if (got[id] !== item.beats[id]) {
        console.log(JSON.stringify({ family: item.family, params: item.params, id, py: item.beats[id], js: got[id] }));
        process.exit(1);
      }
    }
  }
  process.stdout.write("ok");
});
"""
    completed = subprocess.run(
        ["node", "-e", script, str(ROOT / "web" / "narration.js")],
        input=json.dumps(cases),
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert completed.stdout == "ok"


def test_read_failures_use_distinct_copy(monkeypatch, client):
    monkeypatch.setenv("STUDYLAB_VISION", "0")
    off = client.post(
        "/api/lessons",
        files={"image": ("page.png", _png(), "image/png")},
        data={"concept": "sinusoid"},
    ).json()
    assert off["recognition"]["asked"] is None
    assert "没有打开" in off["recognition"]["reason"]

    monkeypatch.setenv("STUDYLAB_VISION", "1")

    def timeout(_image):
        raise httpx.TimeoutException("slow")

    monkeypatch.setattr(vision, "complete", timeout)
    timed = client.post(
        "/api/lessons",
        files={"image": ("page.png", _png(), "image/png")},
    ).json()
    assert "超时" in timed["recognition"]["reason"]
    assert timed["recognition"]["asked"] is None

    def unauthorized(_image):
        request = httpx.Request("POST", "http://127.0.0.1:8010/v1/chat/completions")
        response = httpx.Response(401, request=request)
        raise httpx.HTTPStatusError("no", request=request, response=response)

    monkeypatch.setattr(vision, "complete", unauthorized)
    denied = client.post(
        "/api/lessons",
        files={"image": ("page.png", _png(), "image/png")},
    ).json()
    assert "密钥" in denied["recognition"]["reason"]

    monkeypatch.setattr(vision, "complete", lambda _image: "不是 JSON")
    unparsed = client.post(
        "/api/lessons",
        files={"image": ("page.png", _png(), "image/png")},
    ).json()
    assert "有效结果" in unparsed["recognition"]["reason"]

    header = b"\x89PNG\r\n\x1a\n" + b"\x00" * 24
    broken = client.post(
        "/api/lessons",
        files={"image": ("page.png", header, "image/png")},
    ).json()
    assert "无法解码" in broken["recognition"]["reason"]
    assert "animation" not in broken


def test_api_key_comes_only_from_the_app_variable(monkeypatch):
    monkeypatch.delenv("STUDYLAB_VISION_API_KEY", raising=False)
    monkeypatch.setenv("SPLASH_API_KEY", "splash-secret")
    monkeypatch.setenv("QWEN38_API_KEY", "qwen-secret")
    assert vision._api_key() == ""
    monkeypatch.setenv("STUDYLAB_VISION_API_KEY", "own-secret")
    assert vision._api_key() == "own-secret"


def test_remote_base_is_not_contacted_without_opt_in(monkeypatch):
    monkeypatch.setenv("STUDYLAB_VISION_BASE", "https://example.test")
    monkeypatch.delenv("STUDYLAB_VISION_ALLOW_REMOTE", raising=False)

    def boom(*_args, **_kwargs):
        raise AssertionError("不应把图片发到远端")

    monkeypatch.setattr(httpx, "Client", boom)
    parsed = vision.recognize(_png())
    assert parsed["readFailed"] is True
    assert parsed["reason"] == "remote"
    assert "没有发出" in vision.failure_text(parsed["reason"])


def test_remote_opt_in_allows_the_configured_host(monkeypatch):
    monkeypatch.setenv("STUDYLAB_VISION_BASE", "https://example.test")
    monkeypatch.setenv("STUDYLAB_VISION_ALLOW_REMOTE", "1")
    monkeypatch.setenv("STUDYLAB_VISION_MODEL", "qwen38")
    monkeypatch.setenv("STUDYLAB_VISION_API_KEY", "secret")
    calls = {}

    class FakeResponse:
        status_code = 200

        def raise_for_status(self):
            return None

        def json(self):
            return {
                "choices": [
                    {
                        "message": {
                            "content": '{"concept":"unknown","isSinusoid":"unknown","evidence":""}'
                        }
                    }
                ]
            }

    class FakeClient:
        def __init__(self, *_args, **_kwargs):
            calls["init"] = True

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def post(self, url, headers, json):
            calls["url"] = url
            calls["auth"] = headers.get("Authorization")
            return FakeResponse()

    monkeypatch.setattr(httpx, "Client", FakeClient)
    parsed = vision.recognize(_png())
    assert calls["url"] == "https://example.test/v1/chat/completions"
    assert calls["auth"] == "Bearer secret"
    assert parsed["concept"] == "unknown"
    assert parsed["readFailed"] is False


def test_empty_fake_and_oversized_uploads_are_rejected(client):
    empty = client.post("/api/lessons", files={"image": ("page.png", b"", "image/png")})
    assert empty.status_code == 400
    fake = client.post(
        "/api/lessons",
        files={"image": ("page.png", b"not an image", "text/plain")},
    )
    assert fake.status_code == 400
    typed = client.post(
        "/api/lessons",
        files={"image": ("notes.txt", b"not an image", "image/png")},
    )
    assert typed.status_code == 400
    assert app.content_length_error(str(9 * 1024 * 1024)) == app.IMAGE_ERROR
    assert app.content_length_error(str(app.MAX_IMAGE_BYTES)) is None
    huge = b"\x89PNG\r\n\x1a\n" + b"\x00" * (9 * 1024 * 1024)
    oversized = client.post("/api/lessons", files={"image": ("page.png", huge, "image/png")})
    assert oversized.status_code == 400
    assert oversized.json()["error"] == app.IMAGE_ERROR


def test_lesson_store_keeps_a_bounded_fresh_set(monkeypatch):
    app.LESSONS.clear()
    monkeypatch.setattr(app, "MAX_LESSONS", 2)
    app._remember({"id": "a"})
    app._remember({"id": "b"})
    app._remember({"id": "c"})
    assert list(app.LESSONS) == ["b", "c"]
    clock = {"now": 1000.0}
    monkeypatch.setattr(app.time, "monotonic", lambda: clock["now"])
    app.LESSONS.clear()
    app._remember({"id": "old"})
    clock["now"] += app.LESSON_TTL_SECONDS + 1
    assert app._recall("old") is None
