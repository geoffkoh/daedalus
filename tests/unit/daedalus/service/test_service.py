#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Standard imports
import logging

# Third party imports
import unittest

# Application imports
from daedalus.service.service import ServiceBase


logger = logging.getLogger(__name__)


class TestServiceBase(unittest.TestCase):

    def test_create(self):
        """ Tests the creation of a service """

        my_service = ServiceBase()
        assert my_service is not None, 'Service is created properly'

    # end test_create()

    def test_start(self):
        """ Tests starting the service """

        # Creates the service and runs it
        my_service = ServiceBase()
        my_service.start()

# end class TestServiceBase
