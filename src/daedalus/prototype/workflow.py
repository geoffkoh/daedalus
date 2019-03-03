#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module for the Workflow related class.

In this module there are two basic classes - Workflow and Task.

A Workflow is a collection of Tasks. Each task will have a run() function which can define the
set of operation that it will execute, or it can call some other function which is associated
with the task via the use of a decorator.

==================
Creating Workflows
==================

Workflow can be subclassed, via the following approach.

.. code-block:: python

    class InstallWorkflow(Workflow):
        pass

===============
Declaring tasks
===============

Thereafter one can associate a task with the InstallWorkflow via the following approach

Approach 1: Adding any arbitrary functions as static methods of a task.

.. code-block:: python

    @InstallWorkflow.task('install.init')
    def install(submission_id):
        print('This is my function')

Since the original function is return from here, so one can chain together the same method definition
with multiple workflow classes.

Approach 2: Alternatively one should be able to add Tasks to workflow at instantiation

..code-block:: python

    def MyWorkflow(Workflow):
        pass

    wf = MyWorkflow()

    task1 = Task(func=my_func)
    wf.add_task('install.init', task1)

Approach 3: As part of the definition itself (more richer in case self reference is required)

.. code-block:: python

    def MyTask(Task):
        def func(self, ....):
            pass

    def MyWorkflow(Workflow):
        pass

    wf = MyWorkflow()
    wf.add_task('install.init', MyTask())

==========
Conditions
==========

These are the equivalent of places in a Petri net. In essence it is a dictionary of predicates
which must be satisfy before the associated downstream task can be fired.

=========================
Defining the dependencies
=========================

Ultimately the tasks in a workflow needs to be connected.
This can be done in a variety of methods.

.. code-block:: python

    @InstallWorkflow.and(source=['id1', 'id2'], target=['id3',], condition=[])

    @InstallWorkflow.or(['id1', 'id2'], ['id3',], condition=[])

    (Either id1 or id2 will trigger id3)

If nothing is specified, the return value of the upstream task will be passed as the input
to the downstream task. If one wants a return value to map nicely to kwargs, just return
a dictionary.

Again if the workflow is already instantiated, then the connections can be drawn


===================
Execution Semantics
===================

We only specify a workflow to run without making any assumption where it is going to run on.
The platform for running can be specified in one of two ways:

1. Treating the workflow as a standalone execution plan and run it either locally, on condor or other execution environments
2. The task specifies some simulation environments. Note that we do not allow any asynchronous within the Task


"""

# System imports
import logging
import datetime

# Third party imports

# Application imports


logger = logging.getLogger(__name__)


class TaskMeta(type):
    def __new__(mcs, name, bases, dct):
        my_class = type.__new__(mcs, name, bases, dct)
        if 'func' in dct and callable(dct['func']):
            my_class.func = staticmethod(dct['func'])  # Function as a staticmethod
        return my_class

class Task(metaclass=TaskMeta):
    """ Class to represent a task """

    def __init__(self, func=None, workflow=None):
        """ Constructor """

        if func:
            self.func = staticmethod(func)
        self._workflow = workflow  # Reference to parent workflow instance (not class)

        # Initializes the return value
        self._return_value = None

    # end __init__()

    @property
    def return_value(self):
        """ The return value when it is finished """
        return self._return_value

    @classmethod
    def create_task(cls, func):
        cls.func = func
        return cls

    def run(self):
        """ Runs the task """
        self._return_value = self.func()
        return self._return_value

    # end run()

# end Task


class WorkflowMeta(type):

    def __new__(mcs, name, bases, dct):

        my_class = type.__new__(mcs, name, bases, dct)

        # Creates the task maps according
        my_class.task_map = {}
        my_class.dependency_map = {}

        # Returns the class
        return my_class

    # end __new__()

# end WorkflowMeta()


class Workflow(metaclass=WorkflowMeta):
    """ Base class of a workflow """

    @classmethod
    def task(cls, task_id):
        def register_task(func):
            """ Registers the task to this class """
            task_class = type(task_id, (Task, ), {'func': func})
            cls.task_map[task_id] = task_class
            return func
        return register_task
    # end task

    def __init__(self):
        """ From the class task_map creates the task instances and associates them with the instance """
        # Creates the AP scheduler
        from apscheduler.schedulers.background import BackgroundScheduler
        self._scheduler = BackgroundScheduler()
    # end __init__()

    def start(self):
        """ Runs all the items in the task map """

        # Starts the scheduler
        import datetime

        def timer():
            print(f'my time {datetime.datetime.now()}')

        self._scheduler.add_job(timer, 'interval', seconds=1)
        self._scheduler.start()
        print('Scheduler started')

        for id, task in self.task_map.items():
            t = task()  # Need to create instance
            t.run()

        # Shuts down scheduler
        self._scheduler.shutdown()

# end class Workflow



