import os

from fibers.helper.cache.cache_service import cache_service, cached_function

cache_service.set_main_here()
curr_dir = os.path.dirname(os.path.abspath(__file__))

@cached_function("simple math")
def function_with_cache(a):
    return a * 2


def test_cache_simple():
    cache_path = os.path.join(curr_dir, ".fibers_cache",
                              "test_cache.py.json")
    assert cache_service.cache_kv.cache_path == cache_path
    os.system("rm -r " + os.path.dirname(cache_path))
    function_with_cache(1)
    cache_service.save_cache()
    assert os.path.exists(cache_path)
    cache = cache_service.cache_kv.read_cache(((1,), {}), "simple math")
    assert cache.is_valid()
    assert cache.value == 2
