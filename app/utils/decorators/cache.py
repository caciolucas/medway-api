import hashlib
import json
from functools import wraps

from django.core.cache import cache


def __build_cache_key(prefix, args, kwargs):
    key_elements = {
        "function_name": prefix,
        "args": args,
        "kwargs": kwargs,
    }
    key_str = json.dumps(key_elements, sort_keys=True, default=str)
    return hashlib.md5(key_str.encode("utf-8")).hexdigest()


def cache_result(timeout=300):
    def decorator(func):
        if isinstance(func, classmethod):
            wrapped_func = func.__func__

            @wraps(wrapped_func)
            def wrapper(cls, *args, **kwargs):
                method_prefix = f"{cls.__name__}.{wrapped_func.__name__}"
                cache_key = __build_cache_key(method_prefix, args, kwargs)

                cached_result = cache.get(cache_key)
                if cached_result is not None:
                    return cached_result

                result = wrapped_func(cls, *args, **kwargs)
                cache.set(cache_key, result, timeout)
                return result

            return classmethod(wrapper)
        else:
            raise ValueError(
                "This decorator can't be used on this type of function yet"
            )

    return decorator
