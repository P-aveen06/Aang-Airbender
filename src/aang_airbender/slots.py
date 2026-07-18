from __future__ import annotations

from threading import Lock
from typing import Generic, TypeVar

T = TypeVar("T")


class LatestValueSlot(Generic[T]):
    """A single overwrite-only handoff; it can never accumulate work."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._version = 0
        self._value: T | None = None

    def publish(self, value: T) -> int:
        with self._lock:
            self._version += 1
            self._value = value
            return self._version

    def get_after(self, version: int) -> tuple[int, T] | None:
        with self._lock:
            if self._value is None or self._version <= version:
                return None
            return self._version, self._value
