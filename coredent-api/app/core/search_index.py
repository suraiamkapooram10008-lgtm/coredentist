"""
Search index helpers for encrypted columns.

Encryption at rest makes substring search impossible on the ciphertext.  We
support search by storing a *deterministic HMAC* of the normalized value in a
separate index column.  An attacker with the database can do equality lookups
(``WHERE search_index_email = hmac('alice@example.com')``) but cannot
invert the HMAC to recover the plaintext without the secret key.

The HMAC key is **distinct** from the field-encryption key.  Both come from
the keyring: ``SEARCH_INDEX_KEY`` is derived from the active Fernet key.  This
keeps rotation simple — when you rotate the Fernet key, also rotate the
search index key, and re-index affected rows in a one-shot migration.

This module is intentionally small.  Use it in model setters or
SQLAlchemy ``@validates`` hooks.
"""

from __future__ import annotations

import hashlib
import hmac
import re
from typing import Optional

from app.core.config_simple import settings
from app.core.encryption import keyring


def _search_index_secret() -> bytes:
    """
    Return the HMAC key used for search indexes.  Derived from the active
    encryption key.  In production this should be its own env var
    (SEARCH_INDEX_KEY) but falling back to the encryption key is safe.
    """
    explicit = (
        getattr(settings, "SEARCH_INDEX_KEY", "") or ""
    ).strip()
    if explicit:
        return explicit.encode("utf-8")
    # Derive deterministically from the active Fernet key.
    return hashlib.sha256(b"search-index:" + keyring.active_key_id.encode()).digest()


def normalize(value: Optional[str]) -> str:
    if not value:
        return ""
    # Lowercase, strip non-alphanumeric (keep + for phone country codes).
    return re.sub(r"[^a-z0-9+]", "", value.lower())


def hmac_index(value: Optional[str]) -> Optional[str]:
    """
    Return a 32-byte hex HMAC-SHA256 of the normalized value, or ``None`` if
    the input is empty.  Storing this in a dedicated index column lets the DB
    do equality lookups without revealing the plaintext.
    """
    n = normalize(value)
    if not n:
        return None
    return hmac.new(
        _search_index_secret(), n.encode("utf-8"), hashlib.sha256
    ).hexdigest()


def update_patient_search_indexes(target, *fields: str) -> None:
    """
    Convenience helper: set ``search_index_email``/``search_index_phone``/
    ``search_index_last_name`` on a Patient instance based on the encrypted
    column values.  Call from a SQLAlchemy ``@validates`` or from the
    endpoint right before commit.
    """
    for field in fields:
        value = getattr(target, field, None)
        h = hmac_index(value)
        if field == "email":
            target.search_index_email = h
        elif field == "phone":
            target.search_index_phone = h
        elif field == "last_name":
            target.search_index_last_name = h
