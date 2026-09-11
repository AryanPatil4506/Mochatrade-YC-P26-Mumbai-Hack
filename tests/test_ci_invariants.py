"""CI invariant: fail if `openai` or `langchain` is imported anywhere under
services/gateway/decision/ (the core invariant in CLAUDE.md — the LLM
proposes, a deterministic engine decides). Also passes vacuously if the
directory is ever absent, so this keeps enforcing as the module evolves.
"""

from __future__ import annotations

import re
from pathlib import Path

DECISION_DIR = Path(__file__).parent.parent / "services" / "gateway" / "decision"
_FORBIDDEN = re.compile(r"^\s*(import|from)\s+(openai|langchain)\b", re.MULTILINE)


def test_no_llm_imports_under_gateway_decision():
    if not DECISION_DIR.exists():
        return
    offenders = []
    for path in DECISION_DIR.rglob("*.py"):
        text = path.read_text()
        if _FORBIDDEN.search(text):
            offenders.append(str(path))
    assert not offenders, f"LLM import found under services/gateway/decision/: {offenders}"
