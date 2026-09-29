import threading
import time

_MISSING = object()


class MemoryStore:
    """Thread-safe in-memory cache with per-key expiry and a size limit."""

    def __init__(self, default_ttl=3600, maxsize=1024):
        self.default_ttl = default_ttl
        self._maxsize = maxsize
        self._items = {}  # key -> (value, expires_at or None); insertion order = age
        self._locks = {}  # key -> lock held while that key is being computed
        self._guard = threading.Lock()  # protects _items and _locks

    def get(self, key, default=None):
        with self._guard:
            return self._live(key, default)

    def put(self, key, value, ttl=None):
        """Store `value` for `ttl` seconds (None: until evicted)."""
        with self._guard:
            now = time.monotonic()
            self._items.pop(key, None)  # re-insert so a refreshed key becomes the newest
            if len(self._items) >= self._maxsize:
                for stale in [k for k, (_, exp) in self._items.items() if exp is not None and exp <= now]:
                    self._drop(stale)
            if len(self._items) >= self._maxsize:
                self._drop(next(iter(self._items)))
            self._items[key] = (value, None if ttl is None else now + ttl)

    def forget(self, key):
        with self._guard:
            self._drop(key)

    def forget_prefix(self, prefix):
        """Drop `prefix` itself and every key under `prefix:`."""
        with self._guard:
            for key in [k for k in self._items if k == prefix or k.startswith(prefix + ":")]:
                self._drop(key)

    def flush(self):
        with self._guard:
            self._items.clear()
            self._locks.clear()

    def remember(self, key, ttl, compute, should_cache=None):
        """Cached value for `key`, or `compute()` stored for `ttl()` seconds.

        Callers that miss on the same key at the same moment run `compute` once and
        share the result. Exceptions from `compute`, and results `should_cache` rejects,
        are not cached.
        """
        with self._guard:
            value = self._live(key, _MISSING)
            if value is not _MISSING:
                return value
            lock = self._locks.setdefault(key, threading.Lock())

        with lock:
            with self._guard:  # another caller may have filled it while we waited
                value = self._live(key, _MISSING)
                if value is not _MISSING:
                    return value
            value = compute()
            if should_cache is None or should_cache(value):
                self.put(key, value, ttl())
            return value

    def _live(self, key, default):
        item = self._items.get(key)
        if item is None:
            return default
        value, expires_at = item
        if expires_at is not None and time.monotonic() >= expires_at:
            return default
        return value

    def _drop(self, key):
        self._items.pop(key, None)
        self._locks.pop(key, None)
