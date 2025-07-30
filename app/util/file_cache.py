
import os, json, time, hashlib, threading
from typing import Any, Optional

CACHE_DIR = os.getenv("CACHE_DIR", ".cache")

_lock = threading.Lock()

def _key_to_path(key: str) -> str:
    h = hashlib.sha1(key.encode("utf-8")).hexdigest()
    sub = os.path.join(CACHE_DIR, h[:2], h[2:4])
    os.makedirs(sub, exist_ok=True)
    return os.path.join(sub, h + ".json")

def get(key: str, ttl_seconds: int) -> Optional[Any]:
    if os.getenv("CACHE_BUST") == "1":
        return None
    path = _key_to_path(key)
    if not os.path.exists(path):
        return None
    try:
        stat = os.stat(path)
        if time.time() - stat.st_mtime > ttl_seconds:
            return None
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

def set(key: str, value: Any) -> None:
    path = _key_to_path(key)
    with _lock:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(value, f, ensure_ascii=False, indent=2)
