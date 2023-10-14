from fibers.helper.cache.cache_service import cache_service
from fibers.helper.utils import debugger_is_active

is_debug = debugger_is_active()

def display_chats():
    from fibers.model.chat import ChatLogger
    return ChatLogger()


def display_embedding_search():
    # return IndexingSearchLogger()
    raise NotImplementedError()

def refresh_cache():
    return cache_service.cache_kv.refresh_cache()
