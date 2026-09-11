"""Secrets scanner — custom regex pack + Shannon entropy. Own module, not
Presidio, per CLAUDE.md ("Model & Library Choices").
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass

_PATTERNS: dict[str, re.Pattern] = {
    "AWS_ACCESS_KEY": re.compile(r"AKIA[0-9A-Z]{16}"),
    "AWS_SECRET_KEY": re.compile(r"(?i)aws_secret_access_key\s*[:=]\s*[A-Za-z0-9/+=]{40}"),
    "GITHUB_TOKEN": re.compile(r"gh[pousr]_[A-Za-z0-9]{36,255}"),
    "OPENAI_KEY": re.compile(r"sk-[A-Za-z0-9]{20,}"),
    "SLACK_TOKEN": re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"),
    "PEM_PRIVATE_KEY": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    "JWT": re.compile(r"eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+"),
}

_ENTROPY_TOKEN = re.compile(r"[A-Za-z0-9+/=_-]{20,}")
_ENTROPY_THRESHOLD = 4.5


def _shannon_entropy(s: str) -> float:
    if not s:
        return 0.0
    freq = {}
    for ch in s:
        freq[ch] = freq.get(ch, 0) + 1
    length = len(s)
    return -sum((count / length) * math.log2(count / length) for count in freq.values())


@dataclass
class SecretMatch:
    kind: str
    matched_text: str


def scan_secrets(text: str) -> list[SecretMatch]:
    matches: list[SecretMatch] = []
    for kind, pattern in _PATTERNS.items():
        for m in pattern.finditer(text):
            matches.append(SecretMatch(kind=kind, matched_text=m.group(0)))

    for m in _ENTROPY_TOKEN.finditer(text):
        token = m.group(0)
        if _shannon_entropy(token) > _ENTROPY_THRESHOLD:
            matches.append(SecretMatch(kind="HIGH_ENTROPY_STRING", matched_text=token))

    return matches
