import numpy as np
from PIL.Image import Image
from matplotlib import pyplot as plt

from fibers.helper.image import matplotlib_plot_to_image

"""
# Data generation
"""

def get_experiment_data(noise_scale=0.1):
    """
    Generate data for the experiment.
    Example: x, y = get_experiment_data()
    Return: x of the data, y of the data
    """
    # Generate x in 0 to 10 with 0.01 interval
    x = np.arange(0, 10, 0.01)
    # Generate y = sin(x) + noise
    y = np.sin(x) + np.random.normal(0, noise_scale, len(x))
    return x, y


"""
# Data analysis
"""

def continuity_test(x, y):
    """
    x (np.ndarray): The x-axis data.
    y (np.ndarray): The y-axis data.
    Analyze continuity of the data by the maximal of the second derivative.
    """
    # Calculate the second derivative consider x
    second_derivative = np.gradient(np.gradient(y, x), x)
    # Calculate the maximal of the second derivative
    max_second_derivative = np.max(second_derivative)
    return max_second_derivative


def get_average_and_variance(y):
    """
    y (np.ndarray): The y-axis data.
    Calculate the average and variance of the data.
    """
    average = np.average(y)
    variance = np.var(y)
    return average, variance


"""
# Plot
"""

def get_x_y_plot(x, y) -> Image:
    """
    Get an x-y plot.
    Args:
        x (np.ndarray): The x-axis data.
        y (np.ndarray): The y-axis data.
    Returns:
         The image object.
    """
    plt.plot(x, y)
    # plt to fig
    fig = plt.gcf()
    img = matplotlib_plot_to_image(fig)
    return img

if __name__ == '__main__':
    x, y = get_experiment_data()
    img = get_x_y_plot(x, y)
    img.show()