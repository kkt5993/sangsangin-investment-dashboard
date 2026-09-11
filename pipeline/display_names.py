"""Functional display names for public exports, including cached model prose.

Routes, object keys, persisted notebook IDs and third-party library names stay
stable. This changes text only; source URLs and numerical observations survive.
"""
import re

LABELS = {
    'ASK ARAGORN': '시장 요약',
    'ARAGORN MAP': '업종·자산지도',
    'GLOBAL UNIVERSE': '글로벌 공급망',
    'Images & Words': '주간 기록',
    'AT A GLANCE': '이용 안내',
    'At a Glance': '이용 안내',
    'MAXIMUS': '통합예측',
    'Maximus': '통합예측',
    'DRAGONGLASS': '기업분석',
    'Dragonglass': '기업분석',
    'PRINCIPIUM': '리서치 자료실',
    'Principium': '리서치 자료실',
    'SAURON': '위성·지구관측',
    'Sauron': '위성·지구관측',
    'ARAGORN': '업종·자산지도',
    'TESSERACT': '거시 국면',
    'CROWDING': '시장 쏠림',
    'Crowding': '시장 쏠림',
    'Entity 360': '기업 상세',
    'Entity360': '기업 상세',
    '위성 현장': '위성사진',
}
# ASCII boundaries allow Korean particles and counts immediately after labels,
# while protecting filenames such as SAURON_CONTRACT.md and JS SauronViews.
PATTERN = re.compile(r'(?<![A-Za-z0-9_])(' + '|'.join(map(re.escape, LABELS)) + r')(?![A-Za-z_])')
URL = re.compile(r'https?://[^\s<>"\']+')


def display_text(text):
    parts = []
    cursor = 0
    for match in URL.finditer(text):
        parts.append(PATTERN.sub(lambda m: LABELS[m[0]], text[cursor:match.start()]))
        parts.append(match[0])
        cursor = match.end()
    parts.append(PATTERN.sub(lambda m: LABELS[m[0]], text[cursor:]))
    return ''.join(parts)


def public_labels(value):
    if isinstance(value, dict):
        return {key: public_labels(item) for key, item in value.items()}
    if isinstance(value, list):
        return [public_labels(item) for item in value]
    return display_text(value) if isinstance(value, str) else value
