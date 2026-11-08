"""读图适配器。

只问模型：是不是已支持的知识点，以及图上写明的数字。
旁白、检查题和动画不从模型来。读失败时返回未知，并带上原因，不改成已识别。
密钥只读 STUDYLAB_VISION_API_KEY，不写日志，不进页面。
默认只连接 127.0.0.1 / localhost；远端要显式允许。
"""

from __future__ import annotations

import base64
import json
import math
import os
import re
from io import BytesIO
from urllib.parse import urlparse

from PIL import Image

MAX_EDGE = 1280
TIMEOUT_SECONDS = 120.0
_THINK = re.compile(r"<think>.*?</think>", re.DOTALL)
_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE)

PROMPT = """你在读一张教材或课件的印刷体截图。只判断知识点，并抄图上写明的数字。不要写讲解，不要解题。

concept 只能是 sinusoid、quadratic、logarithm、exponential、trig、unknown。
- sinusoid：图上明确在讲 y = A sin(ωx + φ) 这种正弦型函数。不要把单位圆上的 sin、cos、tan 定义判成 sinusoid。
- quadratic：图上明确在讲二次函数。顶点式给 a、h、k；一般式 y = ax² + bx + c 给 a、b、c。
- logarithm：图上只在讲 y = log_a(x)。base 是底数 a。不要把指数函数判成 logarithm。
- exponential：图上只在讲指数函数 y = a^x。base 是底数 a。不要把对数函数判成 exponential。
- trig：图上在讲 sin、cos、tan 的定义，或单位圆上的三角函数。theta 是图上的角。图上有 ° 或「度」时 thetaUnit 填 deg，否则填 rad。不要把 y = A sin(ωx + φ) 判成 trig。
- 看不清、手写、不是这五个知识点、或一张图里有多道互不相关的题：unknown。

isSinusoid 只能是 yes、no、unknown。只有 concept 为 sinusoid 时才填 yes。
数字只填图上写明的数，没有就 null。不要把旁边例题里无关的数填进来。
φ 若是 π 的倍数，填小数，例如 π/2 填 1.570796。
evidence 是图上的公式原文，不超过 40 个字；没有就空字符串。
"""

SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "lesson_reading",
        "strict": True,
        "schema": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "concept": {
                    "type": "string",
                    "enum": ["sinusoid", "quadratic", "logarithm", "exponential", "trig", "unknown"],
                },
                "isSinusoid": {"type": "string", "enum": ["yes", "no", "unknown"]},
                "A": {"type": ["number", "null"]},
                "omega": {"type": ["number", "null"]},
                "phi": {"type": ["number", "null"]},
                "a": {"type": ["number", "null"]},
                "h": {"type": ["number", "null"]},
                "k": {"type": ["number", "null"]},
                "b": {"type": ["number", "null"]},
                "c": {"type": ["number", "null"]},
                "base": {"type": ["number", "null"]},
                "theta": {"type": ["number", "null"]},
                "thetaUnit": {"type": "string", "enum": ["rad", "deg"]},
                "evidence": {"type": "string"},
            },
            "required": [
                "concept",
                "isSinusoid",
                "A",
                "omega",
                "phi",
                "a",
                "h",
                "k",
                "b",
                "c",
                "base",
                "theta",
                "thetaUnit",
                "evidence",
            ],
        },
    },
}


FAILURE_TEXT = {
    "off": "读图服务没有打开。",
    "undecodable": "这张图片无法解码。请换一张 png、jpeg 或 webp。",
    "unavailable": "读图服务不可用。请确认本机视觉服务已启动后再试。",
    "unauthorized": "读图服务拒绝了密钥。请检查 STUDYLAB_VISION_API_KEY。",
    "timeout": "读图超时。请再试一次。",
    "unparsed": "模型没有返回有效结果。请再试一次，或换一张更清晰的印刷体图。",
    "remote": "读图地址不在本机，图片没有发出。要发到远端，请先设置 STUDYLAB_VISION_ALLOW_REMOTE=1。",
}


class RemoteNotAllowed(Exception):
    """视觉地址不是本机，且没有允许把图片发到远端。"""


def failure_text(reason: str) -> str:
    return FAILURE_TEXT.get(reason, "读图没有成功。请再试一次。")


def _unknown(read_failed: bool, reason: str = "") -> dict:
    return {
        "concept": "unknown",
        "isSinusoid": "unknown",
        "A": None,
        "omega": None,
        "phi": None,
        "a": None,
        "h": None,
        "k": None,
        "b": None,
        "c": None,
        "base": None,
        "theta": None,
        "thetaUnit": "rad",
        "evidence": "",
        "readFailed": read_failed,
        "reason": reason,
    }


def _api_key() -> str:
    return os.environ.get("STUDYLAB_VISION_API_KEY", "").strip()


def _base_url() -> str:
    return os.environ.get("STUDYLAB_VISION_BASE", "http://127.0.0.1:8010").rstrip("/")


def _is_loopback(url: str) -> bool:
    parsed = urlparse(url)
    host = (parsed.hostname or "").strip().lower()
    if parsed.scheme not in {"http", "https"}:
        return False
    return host in {"127.0.0.1", "localhost", "::1"}


def _remote_allowed() -> bool:
    return os.environ.get("STUDYLAB_VISION_ALLOW_REMOTE", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _base_allowed(url: str) -> bool:
    return _is_loopback(url) or _remote_allowed()


def _enabled() -> bool:
    return os.environ.get("STUDYLAB_VISION", "").strip().lower() not in {"0", "off", "false"}


def status() -> dict:
    """给健康检查用。不探测模型，也不返回地址和密钥。"""
    return {
        "enabled": _enabled(),
        "loopback": _is_loopback(_base_url()),
        "remoteAllowed": _remote_allowed(),
    }


def _model_id() -> str:
    chosen = os.environ.get("STUDYLAB_VISION_MODEL", "").strip()
    if chosen:
        return chosen
    headers = {}
    key = _api_key()
    if key:
        headers["Authorization"] = "Bearer " + key
    try:
        import httpx

        response = httpx.get(_base_url() + "/status", headers=headers, timeout=2.0)
        text = response.text
    except Exception:
        return "qwen38"
    if "35B" in text and "27B" not in text:
        return "qwen36"
    return "qwen38"


def _number(value):
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        number = float(value)
        if not math.isfinite(number):
            return None
        return number
    if not isinstance(value, str):
        return None
    text = value.strip().replace(" ", "").replace("pi", "π").replace("PI", "π")
    if text.lower() in {"", "null", "none", "无"}:
        return None
    try:
        number = float(text)
    except ValueError:
        number = _pi_text(text)
    if number is None or not math.isfinite(number):
        return None
    return number


def _pi_text(text: str):
    sign = 1.0
    if text.startswith(("+", "-")):
        sign = -1.0 if text[0] == "-" else 1.0
        text = text[1:]
    if text.count("π") != 1:
        return None
    left, right = text.split("π", 1)
    if right and not right.startswith("/"):
        return None
    try:
        numerator = 1.0 if left == "" else float(left)
        denominator = 1.0 if right in {"", "/"} else float(right[1:])
    except ValueError:
        return None
    if denominator == 0:
        return None
    return sign * numerator / denominator * math.pi


def _evidence(value) -> str:
    if not isinstance(value, str):
        return ""
    text = " ".join(value.split())
    return text[:40]


def parse_model_text(text: str) -> dict | None:
    """把模型正文收成读图结果。没有 JSON 对象就返回 None。"""
    if not isinstance(text, str):
        return None
    body = _THINK.sub("", text).strip()
    body = _FENCE.sub("", body).strip()
    start = body.find("{")
    end = body.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        raw = json.loads(body[start : end + 1])
    except json.JSONDecodeError:
        return None
    if not isinstance(raw, dict):
        return None
    concept = raw.get("concept")
    if concept not in {"sinusoid", "quadratic", "logarithm", "exponential", "trig", "unknown"}:
        concept = "unknown"
    flag = raw.get("isSinusoid")
    if flag not in {"yes", "no", "unknown"}:
        flag = "unknown"
    if concept == "unknown" and flag == "yes":
        concept = "sinusoid"
    if concept != "sinusoid":
        flag = "no" if flag == "yes" else flag
    unit = raw.get("thetaUnit")
    if unit not in {"rad", "deg"}:
        unit = "rad"
    return {
        "concept": concept,
        "isSinusoid": flag,
        "A": _number(raw.get("A")),
        "omega": _number(raw.get("omega")),
        "phi": _number(raw.get("phi")),
        "a": _number(raw.get("a")),
        "h": _number(raw.get("h")),
        "k": _number(raw.get("k")),
        "b": _number(raw.get("b")),
        "c": _number(raw.get("c")),
        "base": _number(raw.get("base")),
        "theta": _number(raw.get("theta")),
        "thetaUnit": unit,
        "evidence": _evidence(raw.get("evidence")),
        "readFailed": False,
        "reason": "",
    }


def _prepare(image_bytes: bytes) -> bytes | None:
    try:
        with Image.open(BytesIO(image_bytes)) as image:
            image.seek(0)
            frame = image.convert("RGB")
            frame.thumbnail((MAX_EDGE, MAX_EDGE))
            buffer = BytesIO()
            frame.save(buffer, format="PNG")
    except Exception:
        return None
    payload = buffer.getvalue()
    if not payload:
        return None
    return payload


def _message_text(payload: dict) -> str:
    choices = payload.get("choices") if isinstance(payload, dict) else None
    if not isinstance(choices, list) or not choices:
        raise ValueError("视觉接口没有返回正文")
    message = choices[0].get("message") if isinstance(choices[0], dict) else None
    content = message.get("content") if isinstance(message, dict) else None
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict) and isinstance(item.get("text"), str):
                parts.append(item["text"])
        return "\n".join(parts)
    raise ValueError("视觉接口没有返回正文")


def _failure_reason(exc: Exception) -> str:
    import httpx

    if isinstance(exc, httpx.TimeoutException):
        return "timeout"
    if isinstance(exc, httpx.HTTPStatusError):
        status_code = exc.response.status_code if exc.response is not None else 0
        if status_code in {401, 403}:
            return "unauthorized"
    return "unavailable"


def complete(image_bytes: bytes) -> str:
    """把图片交给视觉接口，返回模型正文。非本机地址在未允许时直接拒绝。"""
    if not _base_allowed(_base_url()):
        raise RemoteNotAllowed()
    import httpx

    encoded = base64.b64encode(image_bytes).decode("ascii")
    model = _model_id()
    body = {
        "model": model,
        "temperature": 0,
        "max_tokens": 400,
        "chat_template_kwargs": {"enable_thinking": False},
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": PROMPT},
                    {
                        "type": "image_url",
                        "image_url": {"url": "data:image/png;base64," + encoded},
                    },
                ],
            }
        ],
    }
    headers = {"Content-Type": "application/json"}
    key = _api_key()
    if key:
        headers["Authorization"] = "Bearer " + key
    url = _base_url() + "/v1/chat/completions"
    with httpx.Client(timeout=TIMEOUT_SECONDS) as client:
        response = client.post(url, headers=headers, json={**body, "response_format": SCHEMA})
        if response.status_code >= 400:
            response = client.post(url, headers=headers, json=body)
        response.raise_for_status()
        return _message_text(response.json())


def recognize(image_bytes: bytes) -> dict:
    if not isinstance(image_bytes, (bytes, bytearray)):
        raise TypeError("image_bytes 必须是字节")
    if not _enabled():
        return _unknown(True, "off")
    prepared = _prepare(bytes(image_bytes))
    if prepared is None:
        return _unknown(True, "undecodable")
    try:
        text = complete(prepared)
    except RemoteNotAllowed:
        return _unknown(True, "remote")
    except Exception as exc:
        return _unknown(True, _failure_reason(exc))
    parsed = parse_model_text(text)
    if parsed is None:
        return _unknown(True, "unparsed")
    return parsed
