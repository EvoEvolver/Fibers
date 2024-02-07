import matplotlib.pyplot as plt
import numpy as np

from fibers.model.chat import Chat

from PIL import Image



"""
# Large language model and vision models
"""


def call_chat_model(prompt) -> str:
    """
    Call the chat model.
    :param prompt: The prompt for the language model.
    :return: The response from the chat model.
    """
    chat = Chat()
    chat.add_user_message(prompt)
    res = chat.complete_chat()
    return res


def ask_vision_model(image: Image, question: str) -> bool:
    """
    Ask the vision model a question with answer being True or False.
    :param image: The image for the vision model.
    :param question: The question for the vision model to answer.
    :return: The response from the vision model with answer being True or False.
    """
    chat = Chat(system_message="You are a helpful assistant who only answer in `yes` of `no`")
    chat.add_image_message_by_obj(image)
    chat.add_user_message(question)
    res = chat.complete_chat()
    if "yes" in res.lower():
        return True
    else:
        return False


"""
# Text and Image Input/Output
"""

def display_image(image: Image):
    """
    Display an image.
    :param image: image to display
    :return: None
    """
    plt.imshow(image)
    # axis off
    plt.axis('off')
    plt.show()




if __name__ == '__main__':
    from q_lab import draw_x_y_plot
    img = draw_x_y_plot(np.array([1, 2, 3]), np.array([1, 2, 3]), x_label='X',
                        y_label='Y')
    res = call_vision_model(img, "What is in this image?")
    print(res)


