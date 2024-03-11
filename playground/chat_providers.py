from fibers.model.anthropic_model import set_default_to_anthropic
from fibers.model.chat import Chat
from fibers.model.google_model import set_default_to_google

if __name__ == '__main__':
    try:
        chat = Chat()
        chat.add_user_message("Hello. Who is your developer?")
        res = chat.complete_chat()
        print(res)
    except:
        print("OpenAI model is not available")
    try:
        set_default_to_google()
        chat = Chat()
        chat.add_user_message("Hello. Who is your developer?")
        res = chat.complete_chat()
        print(res)
    except:
        print("Google model is not available")
    try:
        set_default_to_anthropic()
        chat = Chat()
        chat.add_user_message("Hello. Who is your developer?")
        res = chat.complete_chat()
        print(res)
    except Exception as e:
        print("Anthropic model is not available")