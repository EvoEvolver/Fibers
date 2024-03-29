from __future__ import annotations

import hashlib
import json
import os
from typing import Dict, Optional, List, Set

from fibers.helper.json_encoder import FibersEncoder


def get_hash(input: any, type: str) -> str:
    return hashlib.sha1(json.dumps([input, type], cls=FibersEncoder).encode("utf-8")).hexdigest()


class Cache:
    """
    The class for storing cache.
    """

    def __init__(self, value, hash: str, input: any, type: str,
                 meta: Optional[Dict] = None):
        self.value = value
        # self.hash should be the same as get_hash(input, type)
        self.hash: str = hash
        self.input: any = input
        self.type: str = type
        self.meta = meta

    def get_self_dict(self):
        return {
            "value": self.value,
            "hash": self.hash,
            "input": self.input,
            "type": self.type,
            "meta": self.meta
        }

    def set_cache(self, value: any, meta: Optional[Dict] = None):
        self.value = value
        self.meta = meta

    def is_valid(self):
        return self.value is not None


CacheTable = Dict[str, Cache]


def serialize_cache_table(cache_table: Dict[str, Cache]):
    res = []
    for key, cache in cache_table.items():
        res.append(cache.get_self_dict())
    return json.dumps(res, indent=1, cls=FibersEncoder)


class CacheTableKV:
    def __init__(self, cache_path: str):
        self.cache_path = cache_path
        # Map from hash to cache
        self.cache_table: Dict[str, Cache] = self.load_cache_table()
        # List of pending cache
        self.pending_cache: List[Cache] = []
        # List of active cache. Used for garbage collection
        self.active_cache_hash: Set[str] = set()
        #
        self.types_to_refresh: Set[str] = set()
        #
        self.refresh_all: bool = False
        #
        self.types_used: Set[str] = set()

    def save_all_cache_to_file(self):
        self.apply_cache_update()
        if len(self.cache_table) == 0:
            return
        os.makedirs(os.path.dirname(self.cache_path), exist_ok=True)
        with open(self.cache_path, "w") as f:
            f.write(serialize_cache_table(self.cache_table))

    def filter_unused_cache(self) -> int:
        n_removed_cache = 0
        new_cache_table = {}
        for hash, cache in self.cache_table.items():
            if hash in self.active_cache_hash:
                new_cache_table[hash] = cache
            else:
                n_removed_cache += 1
        self.cache_table = new_cache_table
        return n_removed_cache

    def read_cache(self, input: any, type: str, create_cache=True) -> Cache | None:
        hash = get_hash(input, type)
        self.types_used.add(type)
        un_hit = hash not in self.cache_table
        if type in self.types_to_refresh or self.refresh_all:
            un_hit = True
        if un_hit:
            if create_cache:
                new_cache = Cache(None, hash, input, type)
                self.add_cache(new_cache)
                return new_cache
            else:
                return None
        cache_hit = self.cache_table[hash]
        self.active_cache_hash.add(hash)
        return cache_hit

    def add_cache(self, cache: Cache):
        self.pending_cache.append(cache)

    def apply_cache_update(self):
        remaining_cache = []
        for cache in self.pending_cache:
            if cache.is_valid():
                self.active_cache_hash.add(cache.hash)
                self.cache_table[cache.hash] = cache
            else:
                remaining_cache.append(cache)
        self.pending_cache = remaining_cache

    def discard_cache_update(self):
        self.pending_cache = []

    def load_cache_table(self) -> CacheTable:
        if not os.path.exists(self.cache_path):
            return {}
        with open(self.cache_path, "r") as f:
            try:
                cache_list = json.load(f)
            except json.decoder.JSONDecodeError:
                cache_list = []
        cache_table = {}
        for cache_dict in cache_list:
            cache = Cache(cache_dict["value"], cache_dict["hash"], cache_dict["input"],
                          cache_dict["type"], cache_dict["meta"])
            cache_table[cache.hash] = cache
        return cache_table

    def refresh_cache(self, cache_type: str = ""):
        """
        Refresh (delete) all cache of the given type. Usage: `with cache_kv.refresh_cache(cache_type):`.
        :param cache_type: The type of cache to refresh. If type is "", then all cache will be
        refreshed
        :return: A context manager of the refresh
        """
        return RefreshContext(self, cache_type)


class RefreshContext:
    def __init__(self, cache_manager_: CacheTableKV, cache_type: str = ""):
        """
        :param cache_type: The type of cache to refresh. If type is "", then all cache will be
        refreshed
        """
        self.cache_type = cache_type
        self.cache_manager = cache_manager_
        self.already_refreshed = False

    def __enter__(self):
        if self.cache_type != "":
            if self.cache_type not in self.cache_manager.types_to_refresh:
                self.cache_manager.types_to_refresh.add(self.cache_type)
            else:
                self.already_refreshed = True
        else:
            if self.cache_manager.refresh_all:
                self.already_refreshed = True
            else:
                self.cache_manager.refresh_all = True

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.cache_type != "":
            if not self.already_refreshed:
                self.cache_manager.types_to_refresh.remove(self.cache_type)
        else:
            if not self.already_refreshed:
                self.cache_manager.refresh_all = False
