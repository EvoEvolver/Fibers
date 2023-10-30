import ast
import concurrent.futures
import os
import sys

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
    from fibers.helper.cache.cache_service import cache_service

    arg_lists = [list(arg) for arg in args]

    with concurrent.futures.ThreadPoolExecutor(max_workers=n_workers) as executor:
        results = []
        for result in tqdm(executor.map(func, *arg_lists), total=len(arg_lists[0]), desc=func.__name__):
            results.append(result)
            if len(results) % 5 == 4:
                cache_service.save_cache()
    cache_service.save_cache()
    return enumerate(results)


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

if __name__ == "__main__":
    @standard_multi_attempts
    def a():
        print("a")
        raise ValueError("a")


    a()
