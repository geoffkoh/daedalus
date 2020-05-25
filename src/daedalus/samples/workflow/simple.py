#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Samples of simple workflows """

# Standard imports

# Application imports
from daedalus.workflow.workflow import Workflow, register


class SimpleWorkflow(Workflow):
    """ A very simple workflow """

    # Just some very basic stages
    states = ['prepare', 'run', 'evaluate', 'cleanup']

    @register(stage='prepare', name='task_prepare')
    def prepare(self):
        """ Does some simple preparation """
        print('In the prepare task')
    # end prepare()

    @register(stage='run', name='task_run')
    def runtask(self, x: int, y: int):
        """ Runs a simple function """
        result = x + y
        return result
    # end run()

    @register(stage='evaluate', name='task_evaluate')
    def evaluate(self, result: int):
        if (result > 5):
            print("More than 5")
            return True
        else:
            print("Fail")
            return False
    # end evaluate()

    @register(stage="cleanup", name="task_cleanup")
    def cleanup(self):
        """ Simple cleanup function """
        print('Cleaning up. Done')
    # end cleanup

# end class SimpleWorkflow


class ExtendedSimpleWorkflow(SimpleWorkflow):
    """ Extends the simple workflow.
    This is not a very good practice. It only extends the
    stages and tasks and some additional functionality but
    not the blueprint itself.
    """

    def __init__(self):
        """ Simple initializer """
        super().__init__()
        self.blueprint.add_task(stage="prepare",
                                taskname="new_prepare",
                                task=self.prepare)
    # end __init__()


# end class ExtendedSimpleWorkflow
