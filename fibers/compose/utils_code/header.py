import inspect
from functools import wraps
from textwrap import dedent, indent

def get_function_header(function):
    res = ["def", " "]
    # Get the function signature
    signature = inspect.signature(function)
    # Print the function signature
    res.append(function.__name__)
    res.append(str(signature))
    res.append(":\n")
    # Get the function docstring
    docstring = function.__doc__
    if docstring is None:
        docstring = ""
    docstring = dedent(docstring)
    docstring = indent(docstring, "    ")
    if docstring is not None:
        res.append("    \"\"\"")
        res.append(docstring)
        res.append("    \"\"\"\n")
    return "".join(res)


if __name__ == '__main__':
    def decorator(function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            return function(*args, **kwargs)
        return wrapper

    @decorator
    def my_function(param1: int, param2: str = "123") -> float:
        """
        This is a function
        :param param1: some words
        :param param2: some words
        :return:
        """
        # function body
        pass

    # Print the function signature
    print(get_function_header(my_function))
