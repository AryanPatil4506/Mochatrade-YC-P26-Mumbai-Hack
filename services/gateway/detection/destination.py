"""`destination_risk` — from config/allowlists.yaml, per CLAUDE.md."""

from __future__ import annotations

import ipaddress
import re
from pathlib import Path
from urllib.parse import urlparse

import yaml

_ALLOWLISTS_PATH = Path(__file__).resolve().parents[3] / "config" / "allowlists.yaml"


def _load_allowlists() -> dict:
    return yaml.safe_load(_ALLOWLISTS_PATH.read_text())


_LISTS = _load_allowlists()
_HIGH_RISK_PATTERNS = [re.compile(p, re.IGNORECASE) for p in _LISTS["high_risk_patterns"]]
_INTERNAL_CIDRS = [ipaddress.ip_network(c) for c in _LISTS["internal_cidrs"]]


def _extract_host(destination: str) -> str:
    if "@" in destination:
        return destination.rsplit("@", 1)[-1].lower()
    parsed = urlparse(destination if "://" in destination else f"//{destination}")
    return (parsed.hostname or destination).lower()


def _matches_domain_list(host: str, domains: list[str]) -> bool:
    return any(host == d or host.endswith(f".{d}") for d in domains)


def _is_internal(host: str) -> bool:
    if _matches_domain_list(host, _LISTS["internal_domains"]):
        return True
    try:
        addr = ipaddress.ip_address(host)
        return any(addr in cidr for cidr in _INTERNAL_CIDRS)
    except ValueError:
        return False


def classify_destination(destination: str | None, user_request: str) -> int:
    if not destination:
        return 0

    host = _extract_host(destination)

    if _is_internal(host):
        base = 5
    elif _matches_domain_list(host, _LISTS["partner_domains"]):
        base = 30
    elif any(p.search(host) for p in _HIGH_RISK_PATTERNS):
        base = 95
    elif _matches_domain_list(host, _LISTS["free_mail_domains"]):
        base = 80
    else:
        base = 70  # other corporate-looking external domain

    if destination not in user_request:
        base = min(100, base + 20)

    return base
