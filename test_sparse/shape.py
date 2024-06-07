class Point:
    """
    This is a class represent a point in 2D space,
    """
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __add__(self, other):
        if isinstance(other, Point):
            return Point(self.x + other.x, self.y + other.y)
        else:
            raise TypeError('')


class Shape:
    def __init__(self):
        pass
