from datetime import datetime
from typing import List


def get_date(date):
    return date if isinstance(date, datetime) else datetime.fromisoformat(date)


class Lst(List):

    def last(self):
        if len(self) == 0:
            return None
        return self[len(self) - 1]

    def first(self):
        if len(self) == 0:
            return None
        return self[0]

    # def append(self, obj):  # real signature unknown
    #
    #
    # def clear(self, *args, **kwargs):  # real signature unknown
    #     """ Remove all items from list. """
    #     pass
    #
    # def copy(self, *args, **kwargs):  # real signature unknown
    #     """ Return a shallow copy of the list. """
    #     pass
    #
    # def count(self, *args, **kwargs):  # real signature unknown
    #     """ Return number of occurrences of value. """
    #     pass
    #
    # def extend(self, *args, **kwargs):  # real signature unknown
    #     """ Extend list by appending elements from the iterable. """
    #     pass
    #
    # def index(self, *args, **kwargs):  # real signature unknown
    #     """
    #     Return first index of value.
    #
    #     Raises ValueError if the value is not present.
    #     """
    #     pass
    #
    # def insert(self, *args, **kwargs):  # real signature unknown
    #     """ Insert object before index. """
    #     pass
    #
    # def pop(self, *args, **kwargs):  # real signature unknown
    #     """
    #     Remove and return item at index (default last).
    #
    #     Raises IndexError if list is empty or index is out of range.
    #     """
    #     pass
    #
    # def remove(self, *args, **kwargs):  # real signature unknown
    #     """
    #     Remove first occurrence of value.
    #
    #     Raises ValueError if the value is not present.
    #     """
    #     pass
    #
    # def reverse(self, *args, **kwargs):  # real signature unknown
    #     """ Reverse *IN PLACE*. """
    #     pass
    #
    # def sort(self, *args, **kwargs):  # real signature unknown
