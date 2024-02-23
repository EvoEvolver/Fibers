from fibers.model.chat import Chat


def test_image_chat():
    chat = Chat()
    chat.add_user_message("What’s in this image?")
    chat.add_image_message("https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Gfp-wisconsin-madison-the-nature-boardwalk.jpg/2560px-Gfp-wisconsin-madison-the-nature-boardwalk.jpg", from_internet=True)
    res = chat.complete_chat()
    print(res)
