import ast
import concurrent.futures
import os
import sys
from typing import List

from tenacity import retry, stop_after_attempt, wait_fixed, \
    retry_if_exception, stop_after_delay
from tqdm import tqdm


class RobustParse:
    @staticmethod
    def dict(src: str):
        # find first {
        start = src.find("{")
        # find last }
        end = src.rfind("}")
        if start == -1 or end == -1:
            raise ValueError(f"Invalid json: {src}")
        try:
            res = ast.literal_eval(src[start:end + 1])
        except:
            raise ValueError(f"Invalid json: {src}")
        return res

    @staticmethod
    def list(src):
        # find first [
        start = src.find("[")
        # find last ]
        end = src.rfind("]")
        if start == -1 or end == -1:
            raise ValueError(f"Invalid json: {src}")
        try:
            res = ast.literal_eval(src[start:end + 1])
        except:
            raise ValueError(f"Invalid json: {src}")
        return res


def parallel_map(func, *args, n_workers=8):
    # Use concurrent.futures.ThreadPoolExecutor to parallelize
    # Use tqdm to show progress bar
    from fibers.helper.cache.cache_service import caching

    arg_lists = [list(arg) for arg in args]

    with concurrent.futures.ThreadPoolExecutor(max_workers=n_workers) as executor:
        results = []
        for result in tqdm(executor.map(func, *arg_lists), total=len(arg_lists[0]),
                           desc=func.__name__):
            results.append(result)
    caching.save()
    return enumerate(results)


"""
# Nested map
"""


def nested_map(func, nested_list: List[List | any]):
    """
    Apply func to each element in nested_list and return a nested list with the same structure
    Precondition: list nested can only contain either list or non-list
    :param func:
    :param nested_list:
    :return:
    """
    flat_list = []
    add_to_flat_list(flat_list, nested_list)
    flat_res = func(flat_list)
    nested_res = make_nested_list(flat_res, nested_list)
    return nested_res


def add_to_flat_list(flat_list, nested_list):
    if isinstance(nested_list[0], list):
        for nested_list_ in nested_list:
            add_to_flat_list(flat_list, nested_list_)
    else:
        flat_list.extend(nested_list)


def make_nested_list(flattened_res, nested_list):
    if not isinstance(nested_list[0], list):
        return flattened_res
    nested_res = []
    i = 0
    for nested_list_ in nested_list:
        nested_res.append(
            make_nested_list(flattened_res[i: i + len(nested_list_)], nested_list_))
        i += len(nested_list_)
    return nested_res


def test_nested_map():
    before_map = [[[1], [2]], [3, 4, 5]]
    after_map = nested_map(lambda arr: list(map(lambda x: x + 1, arr)), before_map)
    assert after_map == [[[2], [3]], [4, 5, 6]]


"""
# Debug and retry decorator
"""


def debugger_is_active() -> bool:
    """Return if the debugger is currently active"""
    return hasattr(sys, 'gettrace') and sys.gettrace() is not None


def get_main_path():
    return os.path.abspath(sys.argv[0])


standard_multi_attempts = retry(
    wait=wait_fixed(0.5),
    stop=(stop_after_attempt(3) | stop_after_delay(30)),
    retry=retry_if_exception(lambda e: True),
    reraise=False,
)


def test_standard_multi_attempts():
    @standard_multi_attempts
    def a():
        print("a")
        raise ValueError("a")

    a()
