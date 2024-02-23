from fibers.model.chat import Chat
from fibers.model.google_model import set_default_to_google

if __name__ == '__main__':
    set_default_to_google()
    chat = Chat(system_message="You are a helpful assistant who only answer in `yes` of `no`")
    chat.add_user_message("Hello. Are you developed by Baidu?")
    res = chat.complete_chat()
    print(res)