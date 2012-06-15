"""
MPTT exceptions.
"""


class InvalidMove(Exception):
    """
    An invalid node move was attempted.

    For example, attempting to make a node a child of itself.
    """
    pass
