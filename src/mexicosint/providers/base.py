"""Shared provider interface.

Formalizes the shape OpenCageProvider/GeoapifyProvider/IPQualityScoreProvider
already follow by convention: same constructor, a sync lookup() and an async
alookup(). main.py already dispatches to providers polymorphically via
duck-typing (_lookup_cached_geocoder_async, _ipqs_job) - this just makes that
contract explicit and type-checkable.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

import aiohttp

T = TypeVar("T")


class Provider(ABC, Generic[T]):
    source: str

    def __init__(self, api_key: str, timeout: int = 8):
        self.api_key = api_key
        self.timeout = timeout

    @abstractmethod
    def lookup(self, query) -> T | None:
        ...

    @abstractmethod
    async def alookup(self, session: aiohttp.ClientSession, query) -> T | None:
        ...
