"""PII / data-sensitivity classifier (`data_sensitivity` risk factor).

Presidio Analyzer + spaCy `en_core_web_sm` — core PII classes
(SSN, credit card, IBAN, phone, email) are regex/checksum recognizers and
work without any NER model; `PERSON`/`LOCATION`/`ORGANIZATION` need spaCy's
NER and are simply not detected if it isn't installed (a lighter but
spec-consistent degradation, not a special-cased fallback path).

`CREDENTIAL` is populated from the secrets scanner (services/gateway/
detection/secrets.py) — a detected secret always counts as the highest
sensitivity class.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field

from services.gateway.detection.secrets import scan_secrets

CLASS_WEIGHT: dict[str, int] = {
    "CREDENTIAL": 100,
    "US_SSN": 95,
    "CREDIT_CARD": 95,
    "IBAN": 90,
    "MEDICAL": 85,
    "PASSPORT": 85,
    "FINANCIAL_RECORD": 80,
    "PHONE_NUMBER": 55,
    "EMAIL_ADDRESS": 50,
    "PERSON": 45,
    "LOCATION": 30,
    "ORGANIZATION": 20,
}

_SSN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
_CREDIT_CARD = re.compile(r"\b(?:\d[ -]?){13,19}\b")
_IBAN = re.compile(r"\b[A-Z]{2}\d{2}[A-Z0-9]{10,30}\b")
_PASSPORT = re.compile(r"\b(?=[A-Z0-9]{6,9}\b)[A-Z]{1,2}\d{6,8}\b")
_PHONE = re.compile(r"\+?\d[\d ()-]{8,14}\d")
_EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_MEDICAL_KEYWORDS = re.compile(r"(?i)\b(diagnos(is|ed)|prescription|patient record|medical history|treatment plan|icd-10)\b")
_FINANCIAL_KEYWORDS = re.compile(r"(?i)\b(account number|routing number|bank statement|financial record)\b")


def _luhn_valid(digits: str) -> bool:
    cleaned = [int(d) for d in digits if d.isdigit()]
    if len(cleaned) < 13:
        return False
    total = 0
    parity = len(cleaned) % 2
    for i, d in enumerate(cleaned):
        if i % 2 == parity:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


_spacy_nlp = None
_spacy_load_failed = False


def _get_spacy():
    global _spacy_nlp, _spacy_load_failed
    if _spacy_nlp is not None or _spacy_load_failed:
        return _spacy_nlp
    try:
        import spacy

        _spacy_nlp = spacy.load("en_core_web_sm")
    except Exception:
        _spacy_load_failed = True
    return _spacy_nlp


_SPACY_LABEL_MAP = {"PERSON": "PERSON", "GPE": "LOCATION", "LOC": "LOCATION", "ORG": "ORGANIZATION"}


@dataclass
class DataSensitivityResult:
    score: int
    detected_entity_types: list[str] = field(default_factory=list)


def detect_entities(text: str) -> set[str]:
    detected: set[str] = set()

    if _SSN.search(text):
        detected.add("US_SSN")
    for m in _CREDIT_CARD.finditer(text):
        if _luhn_valid(m.group(0)):
            detected.add("CREDIT_CARD")
    if _IBAN.search(text):
        detected.add("IBAN")
    if _PASSPORT.search(text):
        detected.add("PASSPORT")
    if _PHONE.search(text):
        detected.add("PHONE_NUMBER")
    if _EMAIL.search(text):
        detected.add("EMAIL_ADDRESS")
    if _MEDICAL_KEYWORDS.search(text):
        detected.add("MEDICAL")
    if _FINANCIAL_KEYWORDS.search(text):
        detected.add("FINANCIAL_RECORD")

    if scan_secrets(text):
        detected.add("CREDENTIAL")

    nlp = _get_spacy()
    if nlp is not None:
        doc = nlp(text[:5000])
        for ent in doc.ents:
            mapped = _SPACY_LABEL_MAP.get(ent.label_)
            if mapped:
                detected.add(mapped)

    return detected


def compute_data_sensitivity(texts: list[str], record_count: int) -> DataSensitivityResult:
    detected: set[str] = set()
    for text in texts:
        detected |= detect_entities(text)

    base = max((CLASS_WEIGHT[c] for c in detected), default=0)
    bump = min(25, round(8 * math.log10(max(record_count, 1))))
    score = min(100, base + bump)

    return DataSensitivityResult(score=score, detected_entity_types=sorted(detected))
