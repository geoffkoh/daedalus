#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Standard imports
import logging

# Application imports
import daedalus.workflow.workflow as workflow

logger = logging.getLogger(__name__)


class MyCustomWorkflow(workflow.Workflow):
    """ This is a custom workflow """

    stages = ['method', 'instance', 'static', 'class']

    @workflow.register(stage='method')
    def task_method(self):
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

    @staticmethod
    def task_post_staticmethod():
        logger.info('In task_post_staticmethod')
        pass

    @classmethod
    def task_post_classmethod(cls):
        logger.info('In task_post_classmethod')
        pass

    def task_post_method(self):
        logger.info('In task_post_method')
        pass

    def task_post_boundmethod(self):
        logger.info('In task_post_boundmethod')
        pass

# end class MyCustomWorkflow


def test_register_tasks():
    """ Testing of the various tasks """

    # Case 1: Register a static function post class creation
    workflow.register(stage='static')(MyCustomWorkflow.task_post_staticmethod)

    # Case 2: Register a class function post class creation
    workflow.register(stage='class')(MyCustomWorkflow.task_post_classmethod)

    # Case 3: Register a class method post class creation
    workflow.register(stage='method')(MyCustomWorkflow.task_post_method)

    # Case 4: Register a instance method
    wf = MyCustomWorkflow()
    workflow.register(stage='instance')(wf.task_post_boundmethod)

# end test_define_workflow()


def test_inner_class():
    """ Tests the creation of workflow """

    class InnerClass2(workflow.Workflow):

        @workflow.register(stage='add')
        def add(self, x: int, y: int):
            return x + y

    logger.info(InnerClass2.blueprint)

# end test_create()
