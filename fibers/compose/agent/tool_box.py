import matplotlib.pyplot as plt
import numpy as np

from fibers.helper.image import matplotlib_plot_to_image
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


def ask_human(question: str):
    """
    Ask a human a question.
    :param question: The question for the human to answer.
    :return: The response from the human.
    """
    print("Human, please answer the following question:")
    print(question)
    res = input()
    return res



def ask_vision_model_about_data(data: np.array, question) -> bool:
    """
    Plot the data and ask a question about the data shape.
    For example, the number of peaks, or whether the data is nearly periodic.
    The answer is either True or False.
    :param data: a one dimensional numpy array.
    :param question: the question to ask.
    :return: the response to the question.
    """
    image = draw_x_y_plot(np.arange(len(data)), data)
    chat = Chat(
        system_message="You are a helpful assistant who only answer in `yes` of `no`")
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


"""
# Plot
"""

def draw_x_y_plot(x, y, x_label="", y_label="") -> Image:
    """
    Draw an x-y plot.
    Args:
        x (np.ndarray): The x-axis data.
        y (np.ndarray): The y-axis data.
        x_label (str): The label for the x-axis.
        y_label (str): The label for the y-axis.
    :return: The image object.
    """
    plt.plot(x, y)
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    # plt to fig
    fig = plt.gcf()
    img = matplotlib_plot_to_image(fig)
    return img



if __name__ == '__main__':
    from q_lab import draw_x_y_plot
    img = draw_x_y_plot(np.array([1, 2, 3]), np.array([1, 2, 3]), x_label='X',
                        y_label='Y')
    res = ask_vision_model(img, "Is the x-y plot a straight line?")
    print(res)


