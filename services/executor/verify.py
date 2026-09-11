"""Capability token verification — the enforcement point (Enforcement
Boundary layer 3: capability tokens). Every /v1/execute call is checked
here in order: signature -> expiry -> jti replay -> args_sha256 ->
tool/operation match. Any failure raises TokenError with the matching
reason so the API layer can return 403 + the right audit trail.
"""

from __future__ import annotations

import time

from packages.contracts.schemas import ProposedAction
from services.executor.audit.repository import jti_seen, mark_jti_used
from services.gateway.decision.capability import (
    TokenError,
    args_sha256,
    decode_and_verify_signature,
)


def verify_token(token: str, action: ProposedAction) -> dict:
    payload = decode_and_verify_signature(token)  # -> signature_invalid

    if payload["exp"] < int(time.time()):
        raise TokenError("expired")

    if jti_seen(payload["jti"]):
        raise TokenError("replayed")
    mark_jti_used(payload["jti"], used_at=str(time.time()))

    expected_tool = f"{action.tool_name.value}.{action.operation.value}"
    if (
        payload["request_id"] != str(action.request_id)
        or payload["tool"] != expected_tool
        or payload["target"] != action.target_resource
        or payload["args_sha256"] != args_sha256(action.arguments)
    ):
        raise TokenError("args_mismatch")

    return payload
