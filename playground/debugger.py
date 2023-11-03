from fibers import debug
from fibers.helper.cache.cache_service import cached_function, caching
from fibers.model.chat import Chat


@cached_function
def some_function():
    chat = Chat(system_message="You are a useless helpful assistant.")
    chat.add_user_message("Randomly give a number in 0 to 10.")
    res = chat.complete_chat()
    return res


if __name__ == "__main__":
    with debug.display_chats():
        print(some_function())
    caching.save()
    # Because the function is cached, the answer will be the same
    print(some_function())
    print(some_function())
    with debug.refresh_cache():
        # Because the cache is refreshed, the answer will be different
        print(some_function())
