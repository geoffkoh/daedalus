#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Tests the utility functions """

# Standard imports
import logging
import types

# Application imports
from daedalus.workflow.util import (get_callable_name, get_callable_parent,
                                    get_callable_type, get_inner_func,
                                    is_ordered_sublist)

logger = logging.getLogger(__name__)


class InnerClass:
    """ Inner class for testing """

    @staticmethod
    def my_static_method():
        pass

    @classmethod
    def my_class_method(cls):
        pass

    def my_normal_method(self):
        pass

# end class InnerClass


def function1():
    """ Function to aid testing """
    pass
# end function1()


def test_is_ordered_sublist():
    """ Tests the is_ordered_sublist() method """

    # Case 1: Normal case
    list1 = [1, 4, 5]
    list2 = [1, 2, 3, 4, 5]
    assert is_ordered_sublist(list1, list2)

    # Case 2: list1 has items not in list2
    list1 = [1, 4, 6]
    list2 = [1, 2, 3, 4, 5]
    assert not is_ordered_sublist(list1, list2)

    # Case 3: list1 is not in same order as list2
    list1 = [2, 1]
    list2 = [1, 2, 3, 4, 5]
    assert not is_ordered_sublist(list1, list2)

    # Case 4: list1 has multiple items
    list1 = [1, 1, 2]
    list2 = [1, 2, 3, 4, 5]
    assert not is_ordered_sublist(list1, list2)

    # Case 5: Both lists have repeated items
    list1 = [2, 3, 3]
    list2 = [1, 2, 3, 3, 3, 4, 5]
    assert is_ordered_sublist(list1, list2)

# end test_is_ordered_sublist()


def test_get_callable_name():
    """ Tests the function get_callable_name """

    # Case 1: Defines a simple function and gets its name
    assert get_callable_name(function1) == 'function1'

    # Case 2: Gets the various names from class functions
    assert get_callable_name(InnerClass.my_static_method) == 'my_static_method'
    assert get_callable_name(InnerClass.my_class_method) == 'my_class_method'
    assert get_callable_name(InnerClass.my_normal_method) == 'my_normal_method'

    # Case 3: Tests if it can work within a decorator
    def test_wrapper(func):
        assert get_callable_name(func) == "my_static_method"
        return func

    class InnerClass2:
        @test_wrapper
        @staticmethod
        def my_static_method():
            pass

# end test_get_callable_name()


def test_get_callable_parent():
    """ Tests the function get_callable_parent """

    # Calling parents from various functions
    assert get_callable_parent(InnerClass.my_static_method)\
        == ('InnerClass', InnerClass)
    assert get_callable_parent(InnerClass.my_class_method)\
        == ('InnerClass', InnerClass)
    assert get_callable_parent(InnerClass.my_normal_method)\
        == ('InnerClass', InnerClass)
    assert get_callable_parent(function1) == (None, None)

# end test_get_callable_parent()


def test_get_callable_type():
    """ Tests the function get_callable_type() """

    # Case 1: Normal function
    assert get_callable_type(function1) == 'function'

    # Case 2: Static method
    assert get_callable_type(InnerClass.my_static_method) == 'staticmethod'

    # Case 3: Class method
    assert get_callable_type(InnerClass.my_class_method) == 'classmethod'

    # Case 4: Unbound method
    assert get_callable_type(InnerClass.my_normal_method) == 'method'

    # Case 5: Bound method
    my_object = InnerClass()
    assert get_callable_type(my_object.my_normal_method) == 'boundmethod'

    # Case 6: Tests if it can work within a decorator
    def test_wrapper(func):
        assert get_callable_type(func) == "staticmethod"
        return func

    class InnerClass2:
        @test_wrapper
        @staticmethod
        def my_static_method():
            pass

# end test_get_callable_type()


def test_get_inner_func():
    """ Tests the function get_inner_func() """

    # Case 1: Getting from function
    assert isinstance(get_inner_func(InnerClass.my_static_method),
                      types.FunctionType)
    assert isinstance(get_inner_func(InnerClass.my_class_method),
                      types.FunctionType)
    assert isinstance(get_inner_func(InnerClass.my_normal_method),
                      types.FunctionType)

# end test_get_inner_func()
