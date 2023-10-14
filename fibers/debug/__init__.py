from fibers.helper.cache_manage import cache_manager
from fibers.helper.utils import debugger_is_active

is_debug = debugger_is_active()

def display_chats():
    from fibers.model.chat import ChatLogger
    return ChatLogger()


def display_embedding_search():
    # return IndexingSearchLogger()
    raise NotImplementedError()

def refresh_cache():
    return cache_manager.refresh_cache()
