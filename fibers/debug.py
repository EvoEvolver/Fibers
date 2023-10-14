from fibers.helper.cache_manage import cache_manager
from fibers.model.chat import ChatLogger
from fibers.utils import debugger_is_active

is_debug = debugger_is_active()

def display_chats():
    return ChatLogger()


def display_embedding_search():
    # return IndexingSearchLogger()
    raise NotImplementedError()

def refresh_cache():
    return cache_manager.refresh_cache()
