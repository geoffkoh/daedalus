#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Tests the task modules """

# System imports
import logging

# Application imports
from daedalus.workflow.task import Task

logger = logging.getLogger(__name__)


def test_run_func_on_function():
    """ Tests run_func() on functions """

    # Defines a temporary function
    def add(x: int, y: int):
        return x + y

    # Defines a function with no input
    def noop():
        print('Hello World')

    # Case 1: Runs normal function
    context = {'add.x': 3, 'add.y': 5}
    params = {'x': 'add.x', 'y': 'add.y'}
    result = Task._run_func(func=add,
                            parent=None,
                            params=params,
                            context=context)
    assert result == 8

    # Case 2: Runs function where parameter is not in params
    context = {'x': 2, 'y': 3}
    result = Task._run_func(func=add, context=context)
    assert result == 5

    # Case 3: Runs function with no required input
    result = Task._run_func(func=noop,
                            parent=None,
                            params=params,
                            context=context)
    assert result is None

# end test_run_func_on_function()


def test_run_func_on_staticmethod():
    """ Tests run_func() on staticmethods """

    class InnerClass:

        @staticmethod
        def add(x: int, y: int):
            return x + y

    # Case 1: Runs normal function
    context = {'add.x': 3, 'add.y': 5}
    params = {'x': 'add.x', 'y': 'add.y'}
    result = Task._run_func(func=InnerClass.add,
                            parent=None,
                            params=params,
                            context=context)
    assert result == 8

    # Case 2: Runs in the context of a decorator
    test_func = None

    def check_function(func):

        nonlocal test_func
        test_func = func.__func__  # Emulate creation of task

        def __inner_wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return __inner_wrapper

    class InnerClassViaDecorator:

        @check_function
        @staticmethod
        def add(x: int, y: int):
            return x + y

    context = {'x': 2, 'y': 3}
    result = Task._run_func(func=test_func,
                            context=context)
    assert result == 5

# end test_run_func_on_staticmethod()


def test_run_func_on_classmethod():
    """ Tests run_func() on classmethods """

    test_func = None

    def check_function(func):

        nonlocal test_func
        test_func = func.__func__  # Emulate creation of task

        def __inner_wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return __inner_wrapper

    class InnerClass:

        z = 10

        @classmethod
        def add(cls, x: int, y: int):
            return x + y + cls.z

        @check_function
        @classmethod
        def multiply(cls, x: int, y: int):
            return x * y * cls.z

    # Case 1: Runs the classmethod
    context = {'add.x': 3, 'add.y': 5}
    params = {'x': 'add.x', 'y': 'add.y'}
    result = Task._run_func(func=InnerClass.add,
                            params=params,
                            context=context)
    assert result == 18

    # Case 2: Runs in the context of a decorator
    context = {'cls': InnerClass, 'x': 2, 'y': 3}
    result = Task._run_func(func=test_func,
                            context=context)
    assert result == 60

# end test_run_func_on_classmethod()


def test_run_func_on_method():
    """ Tests run_func() on methods (both bounded and unbounded) """

    test_func = None

    def check_function(func):

        nonlocal test_func
        test_func = func  # Emulate creation of task

        def __inner_wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return __inner_wrapper

    class InnerClass:

        z = 10

        def add(self, x: int, y: int):
            return x + y + self.z

        @check_function
        def multiply(self, x: int, y: int):
            return x * y * self.z

    # Case 1: Runs the normal method
    inner_class = InnerClass()
    context = {'add.x': 3, 'add.y': 5}
    params = {'x': 'add.x', 'y': 'add.y'}
    result = Task._run_func(func=inner_class.add,
                            params=params,
                            context=context)
    assert result == 18

    # Case 2: Runs in the context of a decorator
    context = {'x': 2, 'y': 3}
    result = Task._run_func(func=test_func,
                            parent=inner_class,
                            context=context)
    assert result == 60

# end test_run_func_on_method()
