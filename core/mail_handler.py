from __future__ import annotations


def fetch_unread_messages(*args, **kwargs):
    raise NotImplementedError


def parse_message(raw_message: object) -> dict:
    raise NotImplementedError


def apply_label(message_id: str, label: str, *args, **kwargs) -> None:
    raise NotImplementedError


def archive_message(message_id: str, *args, **kwargs) -> None:
    raise NotImplementedError

