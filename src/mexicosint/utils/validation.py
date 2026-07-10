"""Validation helpers used by the command-line interface."""

from __future__ import annotations

import socket


def is_valid_ip(value: str) -> bool:
    try:
        socket.inet_aton(value)
        return True
    except OSError:
        try:
            socket.inet_pton(socket.AF_INET6, value)
            return True
        except OSError:
            return False
