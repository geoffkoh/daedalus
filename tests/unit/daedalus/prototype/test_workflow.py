#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Standard imports
import logging

# Third party imports
import unittest

# Application imports
import daedalus.prototype.workflow as workflow


logger = logging.getLogger(__name__)


class TestTask(unittest.TestCase):
    """ Test class for the Task functions """

    def test_register_function_by_decorator(self):

        print('')

        # Declares some workflow classes
        class TestWorkflow(workflow.Workflow):
            pass

        class TestWorkflow2(workflow.Workflow):
            pass

        class SleepWorkflow(workflow.Workflow):
            pass

        # Checks that the task_map for workflows are all different
        print(id(workflow.Workflow.task_map))
        print(id(TestWorkflow.task_map))
        print(id(TestWorkflow2.task_map))

        @TestWorkflow.task('init')
        def init():
            print('This is in init()')

        @TestWorkflow2.task('reg')
        def reg():
            print('This is in reg()')

        @TestWorkflow.task('orig_sim')
        @TestWorkflow2.task('sim')
        def simulate():
            print('This is in sim()')

        def dummy():
            print('This is a dummy function')

        @SleepWorkflow.task('sleep')
        def sleep_task():
            import time
            time.sleep(2)

        # Prints out the class task list
        print(TestWorkflow)
        print(TestWorkflow.task_map)
        print(TestWorkflow2)
        print(TestWorkflow2.task_map)

        wf1 = TestWorkflow()
        wf2 = TestWorkflow2()
        wf3 = TestWorkflow2()

        # Checking the instance task_map
        print('Checking on task map for wf1')
        print(wf1.task_map)

        print('Checking on task map for wf2')
        print(wf2.task_map)

        print('Checking on task map for wf3')
        print(wf3.task_map)

        # Runs the workflow
        print('Calling workflow1')
        wf1.start()

        print('Calling workflow2')
        wf2.start()

        print('Calling workflow3')
        wf3.start()

        # Starts the sleeping workflow
        sleep_wf = SleepWorkflow()
        print('Calling Sleeping workflow')
        sleep_wf.start()


    # end test_register_function()

    def test_func_signature(self):
        """ Tests some of the function signature functions """

        def my_func(arg1:int, arg2:str, arg3:str=None, arg4:str=None) -> int:
            pass

        # Tries inspecting the function
        import inspect
        signature = inspect.signature(my_func)
        print(my_func.__annotations__)
        for name, param in signature.parameters.items():
            print('Inspecting types')
            print(name)
            print(param.kind)



