#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Standard imports
import logging
import inspect

# Application imports
import daedalus.workflow.workflow as workflow
import daedalus.workflow.blueprint as blueprint
import daedalus.workflow.task as task

logger = logging.getLogger(__name__)


class MyCustomWorkflow(workflow.Workflow):
    """ This is a custom workflow """

    stages = ['method', 'bound', 'static', 'class']

    @workflow.register(stage='method')
    def task_method(self):
        pass 

    @workflow.register(stage='bound')
    def task_boundmethod(self):
        pass

    @workflow.register(stage='static')
    @staticmethod
    def task_static():
        logger.info('In task_static()')
        pass

    @workflow.register(stage='class')
    @classmethod
    def task_classmethod(cls):
        logger.info('In task_classmethod()')
        pass

# end class MyCustomWorkflow


class TestWorkflow:
    """ Test class for workflow """

    def test_define_workflow(self):
        """ Tests to define a new workflow """

        logger.info(MyCustomWorkflow.blueprint)

    # end test_define_workflow()

    def test_create(self):
        """ Tests the creation of workflow """

        assert True

    # end test_create()

# end class TestWorkflow