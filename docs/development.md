# Overall

IDE recommendation: PyCharm

Docstring style: rst

## DocInPy

Please use the [Moduler](https://m.evoevo.org) style for adding sections in the codes. 


# Classes

## Knowledge storage
`Node`: The node of knowledge. It only contains the knowledge itself.

`Tree`: The collection of the references to `Node` objects. It contains **the relationship among knowledge**. It includes parents, children and path in the tree structure.

## Indexing
`Indexing`: The class for storing indexing.

## Cache

`CacheService`: The class for managing the cache of expensive tasks.

`cache_service`: The instance of `CacheService` for the whole program. You should import it whenever you want to read and write the caches.

You can use `@cached_function("type of cache")` to wrap a function that generates a cache. The cache will be stored in the `cache_service`.

When you want to discard a certain type of cache. You can use `with cache_manager.refresh_cache(cache_type: str):` to wrap the code that generates the cache. This will disable the cache of the type `cache_type`.

## Debug

In the `debug` module, many useful function for revealing the intermediate results are provided. You can use them to debug the program. For example:
```python
from fibers.debug import display_chats
with display_chats():
    some_code()
```
All the calling of chat completion will be displayed.
