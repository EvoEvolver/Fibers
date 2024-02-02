from io import BytesIO

from PIL.Image import Image, open as open_image
from matplotlib.figure import Figure


def matplotlib_plot_to_image(fig: Figure) -> Image:
    """
    Convert a matplotlib plot to an image.
    :param fig: The matplotlib figure.
    :return: The image.
    """
    img = BytesIO()
    fig.savefig(img, format="png")
    img.seek(0)
    return open_image(img)