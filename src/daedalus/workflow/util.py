#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Utility functions for the workflow package.
"""

# Standard imports
import inspect
import logging
from typing import Callable

logger = logging.getLogger(__name__)


def get_callable_name(obj: Callable):
    """ Gets the name of the callable.

    Args:
        obj (Callable): The callable object.

    Returns:
        Returns the name of the callable function.
    """

    if type(obj).__name__ in ("staticmethod", "classmethod"):
        return obj.__func__.__name__
    return obj.__name__


# end get_callable_name()


def get_callable_type(obj: Callable):
    """ Inspects and get the callable type.

    A callable may take one of several forms:
    * Normal function (function)
    * Static method (staticmethod)
    * Class method (classmethod)
    * Bounded method (method)
    * Unbounded method (unboundmethod)

    Each of these callables need to be handled differently
    when registering them in the blueprint and so we
    need to be able to distinguish between them.

    There needs to be special handling for staticmethod
    and classmethod. We can imagine this function to be called
    when the decorators have been executed so we can't simply
    get the type from the type name.

    Note: This does not work for functions belonging to inner classes
    yet.

    Args:
        obj (Callable): The callable object

    Returns:
        One of the following values: ``function``, ``staticmethod``,
        ``classmethod``, ``boundmethod``, ``method``.
    """

    type_name = type(obj).__name__

    # For unresolved staticmethod or classmethod
    if type_name in ["staticmethod", "classmethod"]:
        return type_name

    # For functions declared within a class
    name = obj.__name__
    parent_name, parent = get_callable_parent(obj)
    if parent and hasattr(parent, name):

        # Set the base type
        type_name = "method"

        # Checks if it is staticmethod/classmethod
        obj_type = parent.__dict__.get(name)
        if type(obj_type).__name__ in ["staticmethod", "classmethod"]:
            return type(obj_type).__name__

        # If it is bounded
        elif hasattr(obj, "__self__"):  # pragma: no cover
            if not inspect.isclass(obj.__self__):
                type_name = "boundmethod"

    # Returns what it originally found
    return type_name


# end get_callable_type()


def get_callable_parent(obj: Callable):
    """ Gets the name and reference of the parent.

    Args:
        obj (Callable): Returns the name and reference
            to the parent type.

    Returns:
        A typle (str, object) of the name and parent.
    """

    func = obj.__func__ if hasattr(obj, "__func__") else obj
    ancestor_list = func.__qualname__.split(".")[:-1]

    name = ".".join(ancestor_list) if ancestor_list else None
    parent = func.__globals__.get(name, None)
    return (name, parent)


# end get_callable_parentname()


def get_inner_func(obj: Callable):
    """ Gets the inner function if available """

    inner_func = obj
    if hasattr(obj, "__func__"):
        inner_func = obj.__func__
    return inner_func


# end get_inner_func()


def is_ordered_sublist(lst1: list, lst2: list):
    """ Checks if lst1 is an ordered sublist of lst2 """

    try:
        index = 0
        for item in lst1:
            location = lst2[index:].index(item)
            index += location + 1
        return True
    except ValueError:
        return False


# end is_ordered_sublist()
