#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
*******
Summary
*******

This is the implementation of workflow within ``daedalus``.


Workflow and Tasks
==================

The task definitions in the workflow are stored in a class attribute ``workflow.task_map``.
This map associates the task id with either the class of a ``Task``, or an actual ``Task`` instance.
The tasks are then either instantiated or copied when the ``start()`` function
is invoked.

Specifying a workflow
=====================

To specify a workflow, we provide a few methods to do so.

Method 1: Using decorators
--------------------------

This is the most basic way of building a workflow. We subclass the ``Workflow``
base class and use its ``@task`` decorator to add functions into its task map

.. code-block:: python

    # Defining a workflow subclass
    class CustomWorkflow(Workflow):
        pass

    # Adding the task to the workflow
    @CustomWorkflow.task('action'):
    def my_action():
        pass

More documentation to be added

Specifying dependencies between the tasks
=========================================

To specify the dependencies between the tasks, we utilize the dependency map.
We only need to specify the parent of a given task.

.. code-block:: python

    # Defining a workflow with dependencies
    class DependencyWorkflow(Workflow):
        pass

    # Adds the tasks and specify their dependencies
    @DependencyWorkflow.task('parent1')
    def parent_task_1():
        pass

    @DependencyWorkflow.task('parent2')
    def parent_task_2():
        pass

    @DependencyWorkflow.task('child1')
    def child_task_1():
        pass

    # Draws the dependency
    dep1 = Dependency()
    DependencyWorkflow.add_dependency('child1',
                                      args = { 'arg1': expr('parent1.return_value'),
                                               'arg2': expr('parent2.return_value'),
                                               'arg3': expr('local.value') },
                                      depends_on = ['parent1', 'parent2'])

Passing Parameters
==================

"""

# Standard imports
import copy
import inspect
import logging

# Third part imports

# Application imports

logger = logging.getLogger(__name__)  # pylint: disable=C0103


class WorkflowError(Exception):
    """ Basic exception for errors raised in this module """
# end class WorkflowError


class WorkflowMeta(type):
    """ Meta type for ``Workflow``.

    This is to allow given functions to be associated with the derived
    subclasses.

    Note: If this is not given, then all the subclasses of ``Workflow`` will
    share the same task map and dependency map. This meta class is required
    to ensure that each different derived class will instantiate and
    maintain their own versions.

    """

    def __new__(cls, name, bases, attr):
        """ Constructor """

        my_class = type.__new__(cls, name, bases, attr)

        if 'task_map' not in attr:
            my_class.task_map = dict()    # pylint: disable=W0212

        if 'dependency_map' not in attr:
            my_class.dependency_map = dict()  # pylint: disable=W0212

        return my_class

    # end __new__()

# end class WorkflowMeta


class Workflow(metaclass=WorkflowMeta):
    """ Base class for a workflow """

    task_map = dict()
    """ Class dictionary to store all the task definitions """

    dependency_map = dict()
    """ Dictionary to map the task dependencies """

    def __init__(self, name=None):
        """ Constructor """

        self._name = name

    # end __init__()

    @classmethod
    def task(cls, task_id):
        """ Decorator to add a task to the workflow.

        Args:
            task_id (str): The id to associate this class to.
            depends_on

        Returns:
            Returns the inner wrapper that takes in the function.
        """

        def register_task(func):
            """ Registers the function into the blueprint. """

            task_class = type(task_id, (Task, ), {'func': func})
            cls.task_map[task_id] = task_class
            return func

        # end register_task()

        return register_task

    # end task()

    @classmethod
    def add_dependency(cls, target, args, name, depends_on):
        """ Class method to draw dependency between child to parent.

        Args:
            target (str): The task id of the child.
            depends_on (str or list): The task id or a list of task id of the parents
            args (dict): A dictionary of parameters to pass to target.
            name (str): The name of this dependency (if empty will construct it)

        Returns:
            Returns a boolean if the dependency is added.
        """

        # Creates the name of the dependency
        if not name:
            depends_on_str = '_'.join(depends_on) if isinstance(depends_on, list) else depends_on
            name = f'{depends_on_str}_{target}'

        # Creates a new dependency object
        # and adds it to the dependency_map
        dependency = Dependency(target, depends_on, args, name)
        cls.dependency_map[name] = dependency

    # end depends_on()

    @classmethod
    def visualize(cls):
        """ Class method to visualize the current task map and the dependencies """
        pass

    # end visualize()

    def add_task(self, task_id, task):
        """ Adds a task into the task_map.

        Args:
            task_id (str): The name of the task.
            task (``Task`` or callable): The class or an instance of the task

        """

        self.task_map[task_id] = task

    # end add_task

    def start(self):
        """ Starts running the workflow """

        for name, task in self.task_map.items():
            logger.info('Running %s', name)
            if inspect.isclass(task):
                curr_task = task()
            else:
                curr_task = copy.deepcopy(task)

            # Runs curr task
            curr_task.run()

        # Runs the task

    # end start()

    def evaluate(self, obj):
        """ Evaluate the expression of a parameter.

        Args:
            obj (``Expression``): The workflow expression to evaluate.

        Returns:
            The value after evaluating the expression object.
        """

        (object_id, attr) = obj.parse()
        if object_id == 'global':  # This is a reserved id
            return self.context[attr]
        else:
            task = self.task_map.get(object_id, None)
            return getattr(task, attr) if task else None

    # end evaluate()

# end class Workflow()


class Expression:
    """ Class to represent an argument expression """

    def __init__(self, expression):
        self._expression = expression

    @property
    def expression(self):
        return self._expression

    def parse(self):
        parts = self._expression.split('.')
        return parts

# end class Expression


class TaskMeta(type):
    """ Metaclass for Task """

    def __new__(cls, name, bases, attrs):
        """ Constructor """

        my_class = type.__new__(cls, name, bases, attrs)
        if 'func' in attrs and callable(attrs['func']):
            func = attrs['func']
            my_class.func = staticmethod(func)
        return my_class

    # end __new__()


class Task(metaclass=TaskMeta):
    """ Basic class for a Task """

    def __init__(self, func=None):
        """ Constructor """

        if func:
            self.func = staticmethod(func)

        # Associate the workflow
        self._workflow = None

        # Initializes the return value
        self._return_value = None

    # end __init__()

    @property
    def return_value(self):
        return self._return_value
    # end return_value()

    @return_value.setter
    def return_value(self, value):
        self._return_value = value
    # return return_value.setter()

    def run(self):
        """ Runs the task and returns the return value """

        self._return_value = self.func(None)
        return self.return_value

    # end run()


    def __str__(self):
        return 'Task'

# end class Task


class Dependency:
    """ The class that models a dependency between any tasks

    This class models the dependency between the tasks, and it also holds contextual information
    to allow for data exchange between the source tasks and the target tasks.

    Args:
        target (Task): The target task.
        depends_on (Task or List of Task): The list of parents that will make this task active.
        args (dict): The arguments to use on the target signature function.
        name (str): Name of this dependency

    """

    def __init__(self, target, depends_on, args=None, name=None):

        self._name = name
        self._source = None
        self._target = None
        self._context = {}

    # end __init__()

    @property
    def name(self):
        """ Returns the name of this dependency """
        return self._name

# end class Dependency