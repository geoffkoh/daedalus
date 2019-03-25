#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Third party imports
import unittest

# Application imports
import daedalus.process.workflow as workflow


class TestTask(unittest.TestCase):
    """ Test class for the Task class. """

    def test_stub(self):
        pass
    # end test_stub()

# end class TestTask


class TestWorkflow(unittest.TestCase):
    """ Test class for the Workflow class. """

    def test_add_task_by_decorator(self):
        """ Tests the adding of tasks via decorator """

        # Define a custom workflow
        class MyWorkflow(workflow.Workflow):
            pass

        class MyWorkflow2(workflow.Workflow):
            pass

        @MyWorkflow.task('task1')
        def task1():
            print('In Task 1')

        @MyWorkflow.task('task2')
        def task2():
            print('In Task 2')

        @MyWorkflow2.task('task3')
        def task3():
            print('In Task 3')

        @MyWorkflow2.task('task4')
        def task4():
            print('In Task 4')

        # Checks that the 2 tasks are in the map
        assert len(MyWorkflow.task_map) == 2
        assert 'task1' in MyWorkflow.task_map
        assert 'task2' in MyWorkflow.task_map

        assert len(MyWorkflow2.task_map) == 2
        assert 'task3' in MyWorkflow2.task_map
        assert 'task4' in MyWorkflow2.task_map

        # Checks that the type of the task_map are Tasks
        for task_id, task in MyWorkflow.task_map.items():
            assert isinstance(task, workflow.TaskMeta)

    # end test_add_task_by_decorator()

    def test_add_task_by_declaration(self):
        """ Tests the adding of tasks by defining the Workflow """

        # Creates the tasks first
        class Task1(workflow.Task):
            def run(self):
                print('In Task 1')

        class Task2(workflow.Task):
            def run(self):
                print('In Task 2')

        # Defines a custom workflow
        class MyWorkflow(workflow.Workflow):
            task_map = {
                'task1': Task1,
                'task2': Task2,
            }
        # end class MyWorkflow

        assert len(MyWorkflow.task_map) == 2

    # end test_add_task_by_declaration()

    def test_add_task_by_construction(self):
        """ Tests the adding of tasks by construction """

        # Creates the tasks first
        class Task1(workflow.Task):
            def run(self):
                print('In Task 1')

        class Task2(workflow.Task):
            def run(self):
                print('In Task 2')

        # Creates a base workflow
        my_workflow = workflow.Workflow()

        # Adds task into the workflow
        my_workflow.add_task('task1', Task1)
        my_workflow.add_task('task2', Task2)

        # Checks that the task map is correct
        assert len(my_workflow.task_map) == 2

    # end test_add_task_by_construction()


    def test_add_dependency(self):
        """ Tests the adding of dependency """

        # Creates the workflow
        class DependencyWorkflow(workflow.Workflow):
            pass

        @DependencyWorkflow.task('parent1')
        def parent1():
            return 'parent1'

        @DependencyWorkflow.task('parent2')
        def parent2():
            return 'parent2'

        @DependencyWorkflow.task('target1')
        def target1(val1, val2):
            print(val1)
            print(val2)

        DependencyWorkflow.add_dependency('target1',
                                          args={'val1': 'parent1.return_value',
                                                'val2': 'parent2.return_value'},
                                          depends_on=['parent1', 'parent2'],
                                          name='place1')

# end class TestTask


