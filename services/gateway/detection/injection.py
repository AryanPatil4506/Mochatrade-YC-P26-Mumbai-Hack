"""Prompt-injection detector (Part 2).

`injection_signal = max(rule_score, classifier_score)` — never averaged, so
a confident rule hit can't be diluted by an uncertain model.

Rules are the primary, always-available signal (rules/injection_patterns.yaml,
seven families). The DeBERTa classifier is an optional confirmer: lazy-loaded,
warmed at startup if available, run with an 800ms timeout via
`asyncio.to_thread`, input capped at 512 tokens. On failure or timeout it
logs once and this module falls back to `detector_mode="rules_only"` —
it must never raise.
"""

from __future__ import annotations

import asyncio
import base64
import codecs
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)

_RULES_PATH = Path(__file__).parent / "rules" / "injection_patterns.yaml"

# Zero-width and bidi-override characters used to hide or reorder text.
_HIDDEN_CHAR_PATTERN = re.compile(
    "[​‌‍‎‏﻿‪‫‬‭‮"
    "⁦⁧⁨⁩]"
)

_BASE64_CANDIDATE = re.compile(r"[A-Za-z0-9+/]{20,}={0,2}")
_HEX_CANDIDATE = re.compile(r"(?:[0-9a-fA-F]{2}){10,}")

CLASSIFIER_MODEL_NAME = "protectai/deberta-v3-base-prompt-injection-v2"
CLASSIFIER_TIMEOUT_SECONDS = 0.8
CLASSIFIER_MAX_TOKENS = 512


def _load_rule_families() -> dict[str, dict]:
    raw = yaml.safe_load(_RULES_PATH.read_text())["families"]
    compiled: dict[str, dict] = {}
    for name, spec in raw.items():
        compiled[name] = {
            "score": spec["score"],
            "patterns": [re.compile(p, re.IGNORECASE) for p in spec["patterns"]],
        }
    return compiled


_FAMILIES = _load_rule_families()


@dataclass
class FamilyMatch:
    family: str
    score: int
    span: tuple[int, int]
    matched_text: str


@dataclass
class RuleScanResult:
    score: int
    families: list[FamilyMatch] = field(default_factory=list)


def _scan_plain(text: str) -> RuleScanResult:
    matches: list[FamilyMatch] = []
    for family, spec in _FAMILIES.items():
        for pattern in spec["patterns"]:
            m = pattern.search(text)
            if m:
                matches.append(FamilyMatch(family=family, score=spec["score"], span=m.span(), matched_text=m.group(0)))
                break  # one match per family is enough to count it as triggered

    if _HIDDEN_CHAR_PATTERN.search(text):
        m = _HIDDEN_CHAR_PATTERN.search(text)
        matches.append(
            FamilyMatch(family="encoding_evasion", score=_FAMILIES["encoding_evasion"]["score"], span=m.span(), matched_text="<hidden-char>")
        )

    if not matches:
        return RuleScanResult(score=0, families=[])

    distinct_families = {m.family for m in matches}
    base_score = max(m.score for m in matches)
    bonus = 10 * (len(distinct_families) - 1)
    score = min(100, base_score + bonus)
    return RuleScanResult(score=score, families=matches)


def _try_decode_evasions(text: str) -> list[str]:
    """Return decoded variants worth re-scanning (base64, hex, rot13)."""

    variants: list[str] = []

    for m in _BASE64_CANDIDATE.finditer(text):
        candidate = m.group(0)
        try:
            decoded = base64.b64decode(candidate, validate=True).decode("utf-8", errors="ignore")
        except Exception:
            continue
        if decoded and decoded.isprintable():
            variants.append(decoded)

    for m in _HEX_CANDIDATE.finditer(text):
        candidate = m.group(0)
        try:
            decoded = bytes.fromhex(candidate).decode("utf-8", errors="ignore")
        except Exception:
            continue
        if decoded and decoded.isprintable():
            variants.append(decoded)

    try:
        rot13 = codecs.decode(text, "rot_13")
        if rot13 != text:
            variants.append(rot13)
    except Exception:
        pass

    return variants


def scan_rules(text: str) -> RuleScanResult:
    """Scan `text` and any encoded payloads it contains."""

    result = _scan_plain(text)
    matched_families = {m.family for m in result.families}

    for decoded in _try_decode_evasions(text):
        decoded_result = _scan_plain(decoded)
        if not decoded_result.families:
            continue
        # A hit only found after decoding is itself evidence of evasion.
        if "encoding_evasion" not in matched_families:
            decoded_result.families.append(
                FamilyMatch(family="encoding_evasion", score=_FAMILIES["encoding_evasion"]["score"], span=(0, 0), matched_text="<decoded>")
            )
        all_families = result.families + decoded_result.families
        distinct = {m.family for m in all_families}
        score = min(100, max(m.score for m in all_families) + 10 * (len(distinct) - 1))
        if score > result.score:
            result = RuleScanResult(score=score, families=all_families)
            matched_families = distinct

    return result


_classifier_pipeline = None
_classifier_load_failed = False
_classifier_load_logged = False


def _select_device() -> int:
    """GPU index if CUDA is available (falls back to CPU, index -1) —
    torch's own availability check, no hardcoded assumption about what's
    on the machine running this.
    """

    try:
        import torch

        return 0 if torch.cuda.is_available() else -1
    except Exception:
        return -1


def warm_classifier() -> None:
    """Best-effort warmup, meant to be called at startup (see scripts/warm_models.py).

    Never raises — failure just means the classifier stays unavailable and
    every future call falls back to rules_only.
    """

    global _classifier_pipeline, _classifier_load_failed, _classifier_load_logged
    if _classifier_pipeline is not None or _classifier_load_failed:
        return
    try:
        from transformers import pipeline

        device = _select_device()
        _classifier_pipeline = pipeline(
            "text-classification", model=CLASSIFIER_MODEL_NAME, truncation=True, max_length=CLASSIFIER_MAX_TOKENS, device=device
        )
    except Exception:
        _classifier_load_failed = True
        if not _classifier_load_logged:
            logger.warning("injection classifier unavailable, falling back to rules_only", exc_info=True)
            _classifier_load_logged = True


def _run_classifier_sync(text: str) -> float | None:
    warm_classifier()
    if _classifier_pipeline is None:
        return None
    try:
        result = _classifier_pipeline(text[: CLASSIFIER_MAX_TOKENS * 4])[0]
        label = result.get("label", "").upper()
        prob = float(result.get("score", 0.0))
        if "INJECTION" in label or label in {"LABEL_1", "1"}:
            return prob
        return 1.0 - prob
    except Exception:
        return None


async def classifier_score(text: str) -> tuple[float | None, str]:
    """Returns (score_0_100_or_None, detector_mode)."""

    global _classifier_load_logged
    try:
        result = await asyncio.wait_for(
            asyncio.to_thread(_run_classifier_sync, text), timeout=CLASSIFIER_TIMEOUT_SECONDS
        )
    except asyncio.TimeoutError:
        if not _classifier_load_logged:
            logger.warning("injection classifier timed out, falling back to rules_only")
            _classifier_load_logged = True
        return None, "rules_only"
    except Exception:
        if not _classifier_load_logged:
            logger.warning("injection classifier errored, falling back to rules_only", exc_info=True)
            _classifier_load_logged = True
        return None, "rules_only"

    if result is None:
        return None, "rules_only"
    return round(result * 100), "rules+classifier"


@dataclass
class InjectionDetectionResult:
    score: int
    families: list[str]
    spans: list[dict]
    detector_mode: str


async def detect_injection(untrusted_texts: list[str]) -> InjectionDetectionResult:
    """Scan every untrusted content source. Rule score never averaged with
    classifier score — `max()` only.
    """

    if not untrusted_texts:
        return InjectionDetectionResult(score=0, families=[], spans=[], detector_mode="rules_only")

    best_rule = RuleScanResult(score=0, families=[])
    for text in untrusted_texts:
        result = scan_rules(text)
        if result.score > best_rule.score:
            best_rule = result

    classifier_results = await asyncio.gather(*(classifier_score(t) for t in untrusted_texts))
    best_classifier = 0.0
    detector_mode = "rules_only"
    for score, mode in classifier_results:
        if score is not None and score > best_classifier:
            best_classifier = score
        if mode == "rules+classifier":
            detector_mode = "rules+classifier"

    final_score = max(best_rule.score, int(best_classifier))
    families = sorted({m.family for m in best_rule.families})
    spans = [
        {"family": m.family, "start": m.span[0], "end": m.span[1], "matched_text": m.matched_text}
        for m in best_rule.families
    ]

    return InjectionDetectionResult(score=final_score, families=families, spans=spans, detector_mode=detector_mode)
