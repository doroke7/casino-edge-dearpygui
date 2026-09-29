"""Method result caching with the same parameters as Hyperf's Cacheable / CachePut / CacheEvict.

    @cacheable(prefix="user", value="#{user_id}", ttl=600, offset=60)
    def get_user(user_id): ...          # cached under "user:<user_id>"

    @cache_put(prefix="user", value="#{user_id}", ttl=600)
    def save_user(user_id, data): ...   # always runs, then refreshes the cache

    @cache_evict(prefix="user", value="#{user_id}")
    def delete_user(user_id): ...       # runs, then drops the cache entry

    @cache_evict(prefix="user", all=True)
    def clear_users(): ...              # runs, then drops every "user:*" entry

Parameters (same names and order as Hyperf, snake_cased):
    prefix   Key prefix. Default: "<module>.<qualname>" of the decorated function.
    value    Key template. `#{name}` is replaced by that argument and `#{user.id}` reads a
             field or dict key of it. Default: all arguments (except self/cls) joined by ":".
             The key is "<prefix>:<value>".
    ttl      Seconds. None: the group's default_ttl.
    listener Name that `delete_listener()` can use to drop this entry later.
    offset   Adds a random 0..offset seconds to ttl so entries do not expire together.
    group    Which store to use, see `register_store()`. Default: "default".
    collect  Accepted for compatibility. Hyperf uses it to record keys so `all=True` can
             find them; MemoryStore scans its keys instead, so it has no effect here.
    skip_cache_results  Results that must not be cached (compared by value and type).

Values live in this process's memory, so they are not shared between processes.
"""

import functools
import inspect
import random
import re

from lib.cache.memory_store import MemoryStore

_PLACEHOLDER = re.compile(r"#\{([^}]+)\}")


_stores = {"default": MemoryStore()}
_listeners = {}  # listener name -> [(group, prefix, value template)]


def register_store(group, store):
    """Use `store` (anything with MemoryStore's methods) for `group`."""
    _stores[group] = store


def get_store(group="default"):
    try:
        return _stores[group]
    except KeyError:
        raise KeyError(f"cache group {group!r} is not registered") from None


def delete_listener(listener, arguments=None):
    """Drop the entries of every cacheable declared with `listener`.

    `arguments` maps argument names to values, filling the `#{...}` placeholders of the
    entry's `value` template (the same as Hyperf's DeleteListenerEvent).
    """
    for group, prefix, value in _listeners.get(listener, ()):
        key = _format_key(prefix, value, dict(arguments or {}))
        get_store(group).forget(key)


def cacheable(prefix=None, value=None, ttl=None, listener=None, offset=0,
              group="default", collect=False, skip_cache_results=None):
    """Return the cached result when there is one, otherwise run the function and cache it."""

    def decorator(func):
        key_prefix = _default_prefix(func) if prefix is None else prefix
        build_key = _key_builder(func, key_prefix, value)
        if listener is not None:
            _listeners.setdefault(listener, []).append((group, key_prefix, value))

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            store = get_store(group)
            return store.remember(
                build_key(args, kwargs),
                lambda: _lifetime(store, ttl, offset),
                lambda: func(*args, **kwargs),
                lambda result: not _skipped(result, skip_cache_results),
            )

        wrapper.cache_key = lambda *args, **kwargs: build_key(args, kwargs)
        return wrapper

    return decorator


def cache_put(prefix=None, value=None, ttl=None, offset=0, group="default", skip_cache_results=None):
    """Always run the function, then store its result (refreshes the cache entry)."""

    def decorator(func):
        build_key = _key_builder(func, _default_prefix(func) if prefix is None else prefix, value)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            key = build_key(args, kwargs)
            result = func(*args, **kwargs)
            if not _skipped(result, skip_cache_results):
                store = get_store(group)
                store.put(key, result, _lifetime(store, ttl, offset))
            return result

        wrapper.cache_key = lambda *args, **kwargs: build_key(args, kwargs)
        return wrapper

    return decorator


def cache_evict(prefix=None, value=None, all=False, group="default", collect=False):
    """Run the function, then drop its cache entry (all=True: every entry under `prefix`)."""

    def decorator(func):
        key_prefix = _default_prefix(func) if prefix is None else prefix
        build_key = _key_builder(func, key_prefix, value)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            key = build_key(args, kwargs)
            result = func(*args, **kwargs)
            store = get_store(group)
            if all:
                store.forget_prefix(key_prefix)
            else:
                store.forget(key)
            return result

        return wrapper

    return decorator


def _default_prefix(func):
    return f"{func.__module__}.{func.__qualname__}"


def _lifetime(store, ttl, offset):
    seconds = store.default_ttl if ttl is None else ttl
    if seconds is None:
        return None
    return seconds + (random.uniform(0, offset) if offset else 0)


def _skipped(result, skip_cache_results):
    return skip_cache_results is not None and any(
        type(result) is type(skip) and result == skip for skip in skip_cache_results
    )


def _key_builder(func, prefix, value):
    signature = inspect.signature(func)

    def build(args, kwargs):
        bound = signature.bind(*args, **kwargs)
        bound.apply_defaults()
        return _format_key(prefix, value, dict(bound.arguments))

    return build


def _format_key(prefix, value, arguments):
    if value is None:
        suffix = ":".join(str(v) for k, v in arguments.items() if k not in ("self", "cls"))
    else:
        suffix = _PLACEHOLDER.sub(lambda m: str(_resolve(m.group(1), arguments)), value)
    return f"{prefix}:{suffix}" if suffix else prefix


def _resolve(path, arguments):
    name, *fields = path.strip().split(".")
    if name not in arguments:
        raise ValueError(f"cache key refers to unknown argument {name!r}")
    current = arguments[name]
    for field in fields:
        current = current[field] if isinstance(current, dict) else getattr(current, field)
    return current
