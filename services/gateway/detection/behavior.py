"""Behavioral anomaly detector (`behavioral_anomaly` risk factor).

`behavioral_anomaly = max(intent_drift, session_rules)`.

Determinism note: the session-window rules are keyed off timestamps carried
on the *input* (`ProposedAction.timestamp`), never `datetime.now()` — so
the detector itself never reads the wall clock, and replaying the same
sequence of actions against a fresh session produces the same scores every
time — no wall-clock reads, matching every other scoring function.

Session state is in-memory, current-session-only, no historical baseline —
deliberately not a trained/unsupervised model (no Isolation Forest or
similar: no baseline data exists to fit one meaningfully). `record_outcome`
must be called once per finalized proposal (after the composite score is
known) so later proposals in the same session can see it; it is not part
of the concurrent detector call itself.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from uuid import UUID

SESSION_WINDOW_SECONDS = 60


def _fallback_text_distance(a: str, b: str) -> float:
    from difflib import SequenceMatcher

    return 1.0 - SequenceMatcher(None, a.lower(), b.lower()).ratio()


_embedder = None
_embedder_failed = False


def _select_device() -> str:
    try:
        import torch

        return "cuda" if torch.cuda.is_available() else "cpu"
    except Exception:
        return "cpu"


def _get_embedder():
    global _embedder, _embedder_failed
    if _embedder is not None or _embedder_failed:
        return _embedder
    try:
        from sentence_transformers import SentenceTransformer

        _embedder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2", device=_select_device())
    except Exception:
        _embedder_failed = True
    return _embedder


def _cosine_distance(u: list[float], v: list[float]) -> float:
    dot = sum(a * b for a, b in zip(u, v))
    norm_u = sum(a * a for a in u) ** 0.5
    norm_v = sum(a * a for a in v) ** 0.5
    if norm_u == 0 or norm_v == 0:
        return 1.0
    return 1.0 - dot / (norm_u * norm_v)


def compute_intent_drift(user_request: str, action_summary: str) -> float:
    model = _get_embedder()
    if model is not None:
        try:
            embeddings = model.encode([user_request, action_summary])
            return max(0.0, min(1.0, _cosine_distance(list(embeddings[0]), list(embeddings[1]))))
        except Exception:
            pass
    return _fallback_text_distance(user_request, action_summary)


def _drift_band(distance: float) -> int:
    if distance <= 0.35:
        return 0
    if distance <= 0.55:
        return 30
    if distance <= 0.75:
        return 65
    return 90


def action_summary(operation: str, tool_name: str, target_resource: str, destination: str | None) -> str:
    return f"{operation} {tool_name} on {target_resource} to {destination or 'internal'}"


@dataclass
class _SessionEvent:
    timestamp: datetime
    tool_name: str
    operation: str
    record_count: int


@dataclass
class _SessionHistory:
    events: list[_SessionEvent] = field(default_factory=list)
    finalized_scores: list[int] = field(default_factory=list)


_session_histories: dict[UUID, _SessionHistory] = {}


def _get_history(session_id: UUID) -> _SessionHistory:
    return _session_histories.setdefault(session_id, _SessionHistory())


def reset_session(session_id: UUID) -> None:
    _session_histories.pop(session_id, None)


def record_outcome(session_id: UUID, risk_score: int) -> None:
    _get_history(session_id).finalized_scores.append(risk_score)


def _session_rules_score(
    session_id: UUID, timestamp: datetime, tool_name: str, operation: str, record_count: int
) -> int:
    history = _get_history(session_id)
    score = 0

    if not any(e.tool_name == tool_name and e.operation == operation for e in history.events):
        score = max(score, 45)

    window_start = timestamp - timedelta(seconds=SESSION_WINDOW_SECONDS)
    recent_tools = {e.tool_name for e in history.events if e.timestamp >= window_start}
    recent_tools.add(tool_name)
    if len(recent_tools) >= 3:
        score = max(score, 55)

    if len(history.events) >= 2:
        last_two = history.events[-2:]
        if all(e.operation == "read" for e in last_two) and operation in ("delete", "send"):
            score = max(score, 70)

    if sum(1 for s in history.finalized_scores if s >= 60) >= 5:
        score = max(score, 75)

    prior_max = max((e.record_count for e in history.events), default=0)
    if prior_max > 0 and record_count > 10 * prior_max:
        score = max(score, 80)

    history.events.append(_SessionEvent(timestamp=timestamp, tool_name=tool_name, operation=operation, record_count=record_count))
    return score


@dataclass
class BehavioralAnomalyResult:
    score: int
    intent_drift: float


def compute_behavioral_anomaly(
    *,
    session_id: UUID,
    timestamp: datetime,
    user_request: str,
    operation: str,
    tool_name: str,
    target_resource: str,
    destination: str | None,
    record_count: int,
) -> BehavioralAnomalyResult:
    summary = action_summary(operation, tool_name, target_resource, destination)
    distance = compute_intent_drift(user_request, summary)
    drift_score = _drift_band(distance)
    session_score = _session_rules_score(session_id, timestamp, tool_name, operation, record_count)
    return BehavioralAnomalyResult(score=max(drift_score, session_score), intent_drift=distance)
