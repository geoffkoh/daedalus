#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Task module.
"""

# Standard imports
import logging
from typing import Callable

# Third party imports
import attr

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

    def __init__(self, func: Callable, params: dict = None, return_value: str = None):
        """ Constructor """

        self._parent = None
        self._func = func
        self._func_type = get_callable_type(func)
        self._params = params or {}
        self._return_value = return_value

        self._status = None

    # end __init__()

    def can_run(self):
        """ Run time check to see if the Task can run """

    # end can_run()

    def run(self):
        """ Runs the underlying function """

        pass

    # end run()


# end class Task
