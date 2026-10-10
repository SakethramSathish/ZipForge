"""
backend/api/cache.py — In-memory job and artifact cache for downloadable assets.
"""

from __future__ import annotations

import time
import uuid
from typing import Any, Dict, Optional


class ArtifactCache:
    """Stores generated archives and extracted files for download."""

    def __init__(self, ttl_seconds: int = 1800) -> None:
        self.ttl = ttl_seconds
        self._store: Dict[str, Dict[str, Any]] = {}

    def set(self, key: str, data: Any) -> None:
        self._prune()
        self._store[key] = {
            "data": data,
            "created_at": time.time(),
        }

    def get(self, key: str) -> Optional[Any]:
        self._prune()
        entry = self._store.get(key)
        return entry["data"] if entry else None

    def create_id(self) -> str:
        return str(uuid.uuid4())

    def _prune(self) -> None:
        now = time.time()
        expired = [k for k, v in self._store.items() if now - v["created_at"] > self.ttl]
        for k in expired:
            self._store.pop(k, None)


cache = ArtifactCache()
