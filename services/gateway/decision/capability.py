"""HMAC-signed, single-use capability tokens — the real authorization
mechanism behind Decision.capability_token. See CLAUDE.md "Enforcement
Boundary" layer 3.

Only the gateway process issues tokens (this module). The executor's
verify.py imports SIGNING_KEY/canonical_json/args_sha256 from here purely as
a plain Python import within the same monorepo — it never receives the key
over the network, and the gateway never calls the executor. In a real
multi-host deployment SIGNING_KEY would come from a shared secret store
rather than being importable code; for this single-repo hackathon build an
env var (SENTINEL_CAPABILITY_SIGNING_KEY) with a documented insecure dev
default is the pragmatic equivalent.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import json
import os
import time
from uuid import UUID, uuid4

SIGNING_KEY = os.environ.get(
    "SENTINEL_CAPABILITY_SIGNING_KEY", "dev-only-insecure-signing-key-change-me"
).encode()

TOKEN_TTL_SECONDS = 120


class TokenError(Exception):
    """Raised by verify.py. `reason` is one of:
    signature_invalid | expired | replayed | args_mismatch
    matching CLAUDE.md's compromised-agent test taxonomy."""

    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(reason)


def canonical_json(data: dict) -> bytes:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), default=str).encode()


def args_sha256(arguments: dict) -> str:
    return hashlib.sha256(canonical_json(arguments)).hexdigest()


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _b64url_decode(data: str) -> bytes:
    return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))


def _sign(payload_bytes: bytes) -> str:
    return _b64url(hmac.new(SIGNING_KEY, payload_bytes, hashlib.sha256).digest())


def issue_token(
    *,
    request_id: UUID,
    decision: str,
    tool_name: str,
    operation: str,
    arguments: dict,
    target_resource: str,
) -> str:
    """`decision` is the state that authorized this: "ALLOW" or "APPROVED"."""

    payload = {
        "request_id": str(request_id),
        "decision": decision,
        "tool": f"{tool_name}.{operation}",
        "args_sha256": args_sha256(arguments),
        "target": target_resource,
        "jti": str(uuid4()),
        "exp": int(time.time()) + TOKEN_TTL_SECONDS,
    }
    payload_bytes = canonical_json(payload)
    return f"{_b64url(payload_bytes)}.{_sign(payload_bytes)}"


def decode_and_verify_signature(token: str) -> dict:
    """Step 1 of verification: well-formed + signature matches. Does not
    check expiry/replay/binding — that's verify.py's job."""

    try:
        payload_b64, signature = token.split(".", 1)
        payload_bytes = _b64url_decode(payload_b64)
    except (ValueError, binascii.Error):
        raise TokenError("signature_invalid")

    if not hmac.compare_digest(signature, _sign(payload_bytes)):
        raise TokenError("signature_invalid")

    try:
        return json.loads(payload_bytes)
    except json.JSONDecodeError:
        raise TokenError("signature_invalid")
