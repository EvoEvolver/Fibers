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


def call_vision_model(image: Image, prompt: str) -> str:
    """
    Call the vision model.
    :param image: The image for the vision model.
    :param prompt: The prompt for the vision model.
    :return: The response from the vision model.
    """
    chat = Chat()
    chat.add_image_message_by_obj(image)
    chat.add_user_message(prompt)
    res = chat.complete_chat()
    return res


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


