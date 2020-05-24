#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Workflow module.

A workflow is a set of tasks that needs to be carried out.
It controls the order in which the tasks are to be executed.

Adopting from gitlab pipelines, tasks are laid
out in a series of stages. Within each stage, the tasks can run in
any order, and all the tasks within a stage must be
completed before any task of the next stage can be triggered
off. Some of the tasks may be marked as skipped if certain
pre-conditions are not satisfied. Some of them may
also be marked as able to fail (for non-critical tasks)

The tasks and stages are stored out in a ``Blueprint``.
Each Workflow class has an instance of the Blueprint.

To define a workflow, we can do it in a few ways:

Approach 1: Define a self-contained Workflow
============================================

In this approach, we extend from the ``Workflow`` class
to create the custom workflow. To specify the
tasks for the workflow, we then override the function
``init_blueprint()`` and that is where one can specify
the various tasks and stages.

Approach 2: Define an empty Workflow and using decorators
=========================================================

Here we allow certain logic to be re-used across multiple
workflows by having their functionality being defined
as regular methods, and associating them with the workflow
blueprint via decorators.

Approach 3: Creating a workflow from configuration
==================================================

Sometimes it will be good to have runtime configuration
being specified not in codes, but in configration yaml files.

==================
Registering a task
==================

==================
Passing parameters
==================

When we define task, there is a need to pass
some values to the underlying function. To do so
each blueprint has a mapping dictionary that is
responsible for finding out within the context
whether there is any parameters that needs to be extracted
and passed to the underlying function. These does not
include instance or class references for classmethod
and bound methods.

Lifecycle of Workflow
=====================

"""

# Standard imports
from collections import defaultdict
from enum import Enum
from functools import wraps
import logging
import inspect
from typing import cast
import uuid
import copy

# Third party imports

# Application imports
from .task import Task
from .blueprint import BluePrint
from .exception import WorkflowError
from .util import (
    get_callable_name,
    get_callable_parent,
    get_inner_func,
    is_ordered_sublist,
)

logger = logging.getLogger(__name__)


def register(
    stage: str,
    name: str = None,
    params: dict = None,
    return_value: str = None,
    workflow_cls: "Workflow" = None,
):
    """ Decorator to register a function as a task into the workflow.

    This decorator can be used within the workflow class definition
    itself. It will try to detect the class within which the function
    is defined and registers the function into the blueprint of the class.

    It does this in a deferred way by storing the blueprint into a
    custom module variable ``_blueprint_cache``. We can't store it in
    the Workflow subclass itself as it does not yet exist. But in its
    meta creation, the Workflow will look for any blueprints in the
    cache and uses it if it exists. As it exists in the module level
    there should not be any namespace clash.

    If it is called outside the context of a Workflow class definition,
    then the parent workflow class needs to be provided.

    Args:
        stage (str): The stage to associate this task with.
        name (str): The name of this task. Uses the function name if not given.
        params: (dict): The input mapping from where we need to get from the context.
        return_value: (str): Location within the context to store the return value.
        workflow_cls (Workflow): The reference to the workflow class.
    """

    def _inner_decorator(func):
        """ Inner decorator that takes in the function itself """

        taskname = name or get_callable_name(func)
        logger.info("Registering %s (%s) in stage %s", func, taskname, stage)

        if workflow_cls:
            if hasattr(workflow_cls, "blueprint") and isinstance(
                workflow_cls.blueprint, BluePrint
            ):
                blueprint = workflow_cls.blueprint
            else:
                raise WorkflowError(
                    f"Trying to register to a non "
                    f"Workflow class ({workflow_cls})"
                )
        else:
            workflow_name = get_callable_parent(func)
            if workflow_name:
                mod = inspect.getmodule(get_inner_func(func))
                cache = getattr(mod, "_blueprint_cache", defaultdict(BluePrint))
                mod._blueprint_cache = cache
                blueprint = cache[workflow_name]
            else:
                raise WorkflowError(f"Fail to register function {func}")

        cast(blueprint, BluePrint)
        if taskname in blueprint.tasknames:
            raise WorkflowError(f"Task {taskname} is already registered")

        # Creates the task and adds it into the blueprint
        task = Task(func, params=params, return_value=return_value)
        logger.info(f'{workflow_name} Adding task {task} into {blueprint}')
        blueprint.add_task(stage=stage, taskname=taskname, task=task)

        @wraps(func)
        def wrapped(*args, **kwargs):
            # Calls the function as per normal
            return func(*args, **kwargs)

        return wrapped

    return _inner_decorator

# end register()


class WorkflowState(Enum):
    """ The various states for a workflow """

    NEW = 1
    READY = 2
    RUNNING = 3
    PAUSED = 4
    COMPLETED = 5

# end class WorkflowState


class WorkflowMeta(type):
    """ Meta class for the Worflow """

    def __new__(cls, name, bases, attr):
        """ Constructor """

        workflow_class = type.__new__(cls, name, bases, attr)

        # Gets the stages either from attr or from the bases
        stages = attr.get("stages", None)
        if stages is None:
            for base in bases:
                stages = getattr(base, "stages", None)
                if stages is not None:
                    break

        # Gets blueprint from module blueprint cache
        # or creates a new one
        mod = inspect.getmodule(workflow_class)
        blueprint = None
        if hasattr(mod, "_blueprint_cache"):
            cache = mod._blueprint_cache
            blueprint = cache.get(name, None)
        if blueprint is None:
            blueprint = BluePrint(stages=stages)

        # If stages has value at this point of time
        # then it means we want to restrict blueprint
        # stages to be the compatible, i.e. the stages
        # in blueprint must be in the same order as
        # that of the class, and that there cannot be
        # a stage in blueprint that is not present in the
        # class
        if stages:
            blueprint_stages = blueprint.stages
            if not is_ordered_sublist(blueprint_stages, stages):
                raise WorkflowError(
                    f"Cached blueprint ({blueprint_stages}) does not "
                    f"have compatible stages as {name} ({stages})"
                )
            # Override blueprint stages with class version
            blueprint.stages = stages
        else:
            stages = copy.copy(blueprint.stages)
            workflow_class.stages = stages
        workflow_class.blueprint = blueprint

        return workflow_class

    # end __new__()

# end class WorkflowMeta


class Workflow(metaclass=WorkflowMeta):
    """ Base class for a Workflow
    """

    # Will be overriden. Each workflow class
    # should have its own blueprint.
    blueprint = BluePrint()

    # Override this to declare the stages
    # But if the stages are the same, then we
    # can re-use. But it is not recommended
    stages = []

    def __init__(self):
        """ Constructor """

        # The unique ID associated with each workflow
        self._id = str(uuid.uuid4())

        # State of the workflow
        self._state = WorkflowState.NEW

        # All the variables associated with the
        # workflow and can be accessible by all the Tasks.
        self._context = None

        # Dictionary to hold the end result of each Task.
        # The key is the name of the task.
        self._result = dict()

        # Instantiate a copy of the stages and blueprint
        self.stages = copy.copy(self.stages)
        # self.blueprint = self.blueprint.instantiate(self, self._context)

    # end __init__()

    @classmethod
    def create_from_settings(cls, settings: dict = None):
        """ Factory method to create a workflow from settings """
        pass

    # end create_from_settings()

# end class Workflow
