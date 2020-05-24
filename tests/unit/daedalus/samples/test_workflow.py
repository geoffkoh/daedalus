#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Tests the workflow samples """

# Standard imports
import logging

# Application imports
from daedalus.workflow.workflow import Workflow
from daedalus.samples.workflow.simple import (
    SimpleWorkflow, 
    ExtendedSimpleWorkflow
)

logger = logging.getLogger(__name__)


def test_simple_workflow():
    """ Tests the simple workflow """

    # Checks that the simple workflow blueprint is not
    # the same as the main one
    logger.info(Workflow.blueprint)
    logger.info(SimpleWorkflow.blueprint)
    logger.info(ExtendedSimpleWorkflow.blueprint)
    assert SimpleWorkflow.blueprint != Workflow.blueprint
    assert SimpleWorkflow.blueprint.task_map != Workflow.blueprint.task_map

    # Adds a stage into Extended
    ExtendedSimpleWorkflow.blueprint.stages.append('additional')
    logger.info(SimpleWorkflow.blueprint)
    logger.info(ExtendedSimpleWorkflow.blueprint)
    logger.info(ExtendedSimpleWorkflow().blueprint)

    # Tests the running of the simple workflow
    simple = SimpleWorkflow()
    results = simple.run()
    logger.info(results)

# end test_simple_workflow()
