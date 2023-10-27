from __future__ import annotations

import inspect
import os
from typing import Callable
from functools import wraps

from fibers.helper.cache.cache_embedding import CacheTableEmbed
from fibers.helper.cache.cache_kv import CacheTableKV
from fibers.helper.utils import get_main_path


def get_cache_path(main_path: str):
    file_name = os.path.basename(main_path)
    dir_name = os.path.dirname(main_path)
    return os.path.join(dir_name, ".fibers_cache", file_name + ".json")


class CacheService:

    def __init__(self):
        cache_path = get_cache_path(get_main_path())
        self.cache_kv: CacheTableKV = CacheTableKV(cache_path)
        self.cache_embed: CacheTableEmbed = CacheTableEmbed(os.path.dirname(cache_path))
        self.cache_kv_other = {self.cache_kv.cache_path: self.cache_kv}
        self.cache_embed_other = {self.cache_kv.cache_path: self.cache_embed}

    def save_cache(self):
        self.cache_kv.save_all_cache_to_file()
        self.cache_embed.save_cache_table()

    def save_used_cache(self):
        n_remove = self.cache_kv.filter_unused_cache()
        if n_remove > 0:
            print(f"Removed {n_remove} unused cache")
        self.cache_kv.save_all_cache_to_file()
        # TODO: save only used cache
        self.cache_embed.save_cache_table()

    def set_main_here(self):
        # get the file path of the caller use inspect
        frame = inspect.stack()[1]
        module = inspect.getmodule(frame[0])
        main_path = os.path.abspath(module.__file__)
        self.load_cache_on_path(main_path)

    def load_cache_on_path(self, main_path):
        cache_path = get_cache_path(main_path)
        cache_dir = os.path.dirname(cache_path)

        if cache_path in self.cache_kv_other:
            self.cache_kv = self.cache_kv_other[cache_path]
        else:
            self.cache_kv = CacheTableKV(cache_path)
            self.cache_kv_other[cache_path] = self.cache_kv

        if cache_dir in self.cache_embed_other:
            self.cache_embed = self.cache_embed_other[cache_dir]
        else:
            self.cache_embed = CacheTableEmbed(cache_dir)
            self.cache_embed_other[cache_dir] = self.cache_embed


cache_service = CacheService()


def cached_function(cache_type_or_function: str | Callable):
    """
    A decorator with argument cache_type. Usage: `@cached_function` or `@cached_function(cache_type)`.
    :param cache_type: An identifier of the cache type. It should be distinct from other cache types.
    """

    if isinstance(cache_type_or_function, str):
        cache_type = cache_type_or_function
    else:
        func = cache_type_or_function
        # Get the function's module name
        module = inspect.getmodule(func)
        cache_type = module.__name__ + "." + func.__name__

    def cached_function_wrapper(func):
        @wraps(func)
        def func_wrapper(*args, **kwargs):
            cache = cache_service.cache_kv.read_cache((args, kwargs), cache_type)
            if cache.is_valid():
                return cache.value
            res = func(*args, **kwargs)
            cache.set_cache(res)
            return res

        return func_wrapper

    if isinstance(cache_type_or_function, str):
        return cached_function_wrapper
    else:
        return cached_function_wrapper(cache_type_or_function)
