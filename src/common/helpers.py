from time import sleep
from typing import Callable, ParamSpec, TypeVar

from django.core.cache import cache

P = ParamSpec("P")
R = TypeVar("R")


def synchronise(
        key: str,
        ttl_seconds: int = 10,
        retries: int | None = None,
        timeout_seconds: int | None = None,
        callback: Callable[P, R] = lambda : {},
        *args: P.args,
        **kwargs: P.kwargs
) -> R:
    """
    Creates a distributed mutex using cache so that race conditions cannot happen. Places a key that is checked before
    running the callable passed to the function. Can optionally be set to wait and try again as a fail open mechanism.
    """
    if cache.has_key(key):
        # Exit if retries exceeded
        if retries is not None and retries <= 0:
            raise RuntimeError("retries exceeded")
        # Wait then try again
        if timeout_seconds is not None and timeout_seconds > 0:
            sleep(timeout_seconds)
        synchronise(key, ttl_seconds, retries-1, timeout_seconds, callback, *args, **kwargs)

    # Set the lock
    cache.set(key, key, ttl_seconds)

    try:
        return callback(*args, **kwargs)
    except BaseException as e:
        cache.delete(key)
        raise e
    finally:
        cache.delete(key)
