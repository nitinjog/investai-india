"""In-memory TTL cache — no external dependencies, Render-compatible."""
import time
import threading
from typing import Any, Optional
import os

_store: dict = {}
_lock = threading.Lock()

DEFAULT_TTL = {
    "prices":  int(os.getenv("CACHE_TTL_PRICES", 900)),
    "fd":      int(os.getenv("CACHE_TTL_FD",     86400)),
    "macro":   int(os.getenv("CACHE_TTL_MACRO",  86400)),
    "news":    int(os.getenv("CACHE_TTL_NEWS",   1800)),
    "gold":    int(os.getenv("CACHE_TTL_GOLD",   1800)),
    "default": 3600,
}

def _ttl_for(key: str) -> int:
    for prefix, ttl in DEFAULT_TTL.items():
        if key.startswith(prefix):
            return ttl
    return DEFAULT_TTL["default"]

def get(key: str) -> Optional[Any]:
    with _lock:
        entry = _store.get(key)
        if entry is None:
            return None
        if time.time() > entry["expires"]:
            del _store[key]
            return None
        return entry["value"]

def set(key: str, value: Any, ttl: Optional[int] = None) -> None:
    ttl = ttl or _ttl_for(key)
    with _lock:
        _store[key] = {"value": value, "expires": time.time() + ttl}

def delete(key: str) -> None:
    with _lock:
        _store.pop(key, None)

def clear_all() -> None:
    with _lock:
        _store.clear()

def stats() -> dict:
    with _lock:
        now = time.time()
        live = {k: v for k, v in _store.items() if v["expires"] > now}
        return {"total_keys": len(_store), "live_keys": len(live)}
