#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Blueprint module.
"""

# Standard imports
import itertools
import logging
from typing import Dict, List

# Third party imports
import attr

# Application imports
from .task import Task

logger = logging.getLogger(__name__)


@attr.s
class BluePrint:
    """ Data structure to hold and organize the Tasks """

    # The list of stages associated with this class
    stages = attr.ib(type=List[str], factory=list)

    # Structure storing the mapping of each stage
    # to an OrderedDict of task_name to task mapping.
    task_map = attr.ib(type=Dict[str, Dict[str, Task]], factory=dict)

    @property
    def tasknames(self):
        """ Returns the list of registered task names """
        inner_list = [list(entry.keys()) for _, entry in self.task_map.items()]
        names = list(itertools.chain.from_iterable(inner_list))
        return names

    # end tasknames()

    def add_task(self, stage: str, taskname: str, task: "Task"):
        """ Adds a task to the workflow """

        if stage not in self.stages:
            self.stages.append(stage)
        if stage not in self.task_map:
            self.task_map[stage] = {}
        self.task_map[stage][taskname] = task

    # end add_task()

# end class BluePrint
