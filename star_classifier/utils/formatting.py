"""Formatting helpers used by UI and services."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

_SUPERSCRIPT_MAP = str.maketrans('-0123456789', '⁻⁰¹²³⁴⁵⁶⁷⁸⁹')


SPECIAL_NUMBERS = {
    1e-4: '10⁻⁴',
    1e-3: '10⁻³',
    1e-2: '10⁻²',
    1e-1: '10⁻¹',
    1.0: '1',
    10.0: '10',
    100.0: '10²',
    1000.0: '10³',
    10000.0: '10⁴',
    100000.0: '10⁵',
    1000000.0: '10⁶',
}


def format_number(value: float | int | None) -> str:
    if value is None:
        return '—'
    value = float(value)
    for special, label in SPECIAL_NUMBERS.items():
        if abs(value - special) < 1e-12:
            return label
    if value.is_integer():
        return str(int(value))
    return f'{value:.6f}'.rstrip('0').rstrip('.')


def format_range(low: float | None, high: float | None) -> str:
    return f'[{format_number(low)}; {format_number(high)}]'



def parse_float(text: str) -> float:
    normalized = text.strip().replace(',', '.')
    replacements = {
        '10⁻⁴': '1e-4',
        '10⁻³': '1e-3',
        '10⁻²': '1e-2',
        '10⁻¹': '1e-1',
        '10²': '1e2',
        '10³': '1e3',
        '10⁴': '1e4',
        '10⁵': '1e5',
        '10⁶': '1e6',
    }
    for src, target in replacements.items():
        normalized = normalized.replace(src, target)
    return float(normalized)



def knowledge_signature(data: dict) -> str:
    payload = json.dumps(data, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(payload.encode('utf-8')).hexdigest()



def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
