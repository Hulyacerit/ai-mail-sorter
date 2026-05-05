from __future__ import annotations

import os
from typing import Any


def get_env(name: str, default: str | None = None) -> str | None:
    return os.getenv(name, default)


def is_blank(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip() == ""
    return False

