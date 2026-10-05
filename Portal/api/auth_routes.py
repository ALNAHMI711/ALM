"""Small authentication-domain helpers used by the YOW portal.

The persistence and HTTP integration remain in main.py until the authentication
contract is fully covered by tests.
"""

from __future__ import annotations

import re

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def normalize_email(value: str) -> str:
    email = value.strip().lower()
    if not EMAIL_PATTERN.fullmatch(email):
        raise ValueError("invalid email")
    return email


def is_valid_account_id(value: str) -> bool:
    return 8 <= len(value) <= 64 and value.isprintable() and not any(ch.isspace() for ch in value)
