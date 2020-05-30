#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Task module.
"""

# Standard imports
import logging
import inspect
from typing import Callable

# Third party imports

# Application imports
from .util import get_callable_type

logger = logging.getLogger(__name__)


class Task:
    """ Class that represents a task.

    It is a thin wrapper on top of an object that is Callable.
    Each workflow class will have an instance of the ``BluePrint``, which
    essentially defines all the stages and tasks and their order
    or execution.

    When an workflow instantiates itself, there is a need to clone the
    blueprint and the tasks so that any other changes by other instances
    of the same workflow does not accidentally change this instance.
    The new copies of the blueprint and tasks will then need to be
    bounded to the instance of the workflow.

    """

    can_fail = False  # Flag to indicate if this Task is allowed to fail

    def __init__(self,
                 func: Callable,
                 name: str,
                 parent: object = None,
                 params: dict = None,
                 return_value: str = None):
        """ Constructor """

        self._parent = parent
        self._func = func
        self._name = name
        self._params = params or {}
        self._return_value = return_value

        self._status = None

    # end __init__()

    def run_task(self, context: dict = None):
        """ Runs the underlying function using the context """

        result = self._run_func(func=self._func,
                                parent=self._parent,
                                params=self._params,
                                context=context)

        key = self._name
        if (self._return_value):
            key = self._return_value
        context[key] = result

    # end run()

    @staticmethod
    def _run_func(func: Callable,
                  parent: object = None,
                  params: dict = None,
                  context: dict = None):
        """ Runs the underlying function.

        Runs the underlying function. It will map the params,
        which is a dictionary of parameter mapping and gets the
        contents from the context before passing them into the function.

        If the parent is not None, then it will assign it as the
        first element of the keyword list. So the determination whether
        it is a method or just a function is determined outside. This
        is typically only used if the task is created within the registration
        decorator before the Workflow class has even been created.
        """

        # Set default values
        params = params or {}
        context = context or {}

        # Gets the arg list
        kwargs = {}
        signature = inspect.signature(func)
        func_arg_list = list(signature.parameters.keys())

        # To handle unbounded methods
        start_index = 0
        if parent and func_arg_list:
            first_arg = func_arg_list[0]
            kwargs[first_arg] = parent
            start_index = 1

        # Handles the rest of the arguments
        for arg in func_arg_list[start_index:]:
            arg_in_context = params.get(arg, arg)
            value_from_context = context.get(arg_in_context, None)
            kwargs[arg] = value_from_context

        # Calls the function
        logger.debug('Running task with parameters %s', kwargs)
        result = func(**kwargs)

        return result

    # end _run_func()

# end class Task
