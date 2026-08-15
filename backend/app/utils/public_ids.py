"""Human-friendly, collision-safe public identifiers.

API-facing IDs (e.g. "P123", "D17", "DLV42") are decoupled from internal
integer primary keys so that numeric ID enumeration is not exposed.
"""

import secrets
import string

_ALPHABET = string.ascii_uppercase + string.digits

_PREFIXES = {
    "user": "U",
    "driver": "D",
    "parcel": "P",
    "delivery": "DLV",
    "request": "X",
    "feedback": "FB",
}


def _random_part(length: int = 5) -> str:
    return "".join(secrets.choice(_ALPHABET) for _ in range(length))


def new_public_id(kind: str) -> str:
    prefix = _PREFIXES.get(kind, "X")
    return f"{prefix}{_random_part()}"
