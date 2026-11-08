"""Live vision smoke check. Requires the local vision service on 127.0.0.1:8010 and its key."""

import json
import sys
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'server'))

import vision

FONT_LATIN = '/System/Library/Fonts/Supplemental/Arial.ttf'
FONT_CJK = '/System/Library/Fonts/STHeiti Medium.ttc'

def render(text, font_path, size=(1000, 300), font_size=48):
    image = Image.new('RGB', size, 'white')
    font = ImageFont.truetype(font_path, font_size)
    ImageDraw.Draw(image).text((30, 70), text, fill='black', font=font)
    buffer = BytesIO()
    image.save(buffer, format='PNG')
    return buffer.getvalue()

CASES = {
    'sinusoid': render('y = 2 sin(3x + pi/2)', FONT_LATIN),
    'quadratic': render('y = x^2 - 2x + 1', FONT_LATIN),
    'logarithm': render('y = log_3(x)', FONT_LATIN),
    'chinese': render('例 已知函数 y = 2sin(3x + π/2)', FONT_CJK, font_size=46),
    'general': render('y = A sin(w x + phi)', FONT_LATIN),
    'multi': render('y = 2 sin(3x + pi/2)\ny = x^2 - 2x + 1', FONT_LATIN, size=(1000, 360)),
    'unrelated': render('Hello world, this is a history slide', FONT_LATIN),
}

for name, payload in CASES.items():
    result = vision.recognize(payload)
    print(name, json.dumps(result, ensure_ascii=False))