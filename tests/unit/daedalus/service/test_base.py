#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Test module for Service """

# Standard imports
import logging

# Application imports
from daedalus.service.base import Service, add_job

logger = logging.getLogger(__name__)


class SampleService(Service):
    @add_job(name='sample')
    def sample(self):
        pass
# end class SampleService

logger.info(_service_cache)

def test_add_job_decorator():
    """ Tests the decorator functions """

    s = SampleService()

# end test_add_job_decorator()


class TestService:
    """ Test class for a service """

    def test_base_service(self):
        """ Tests the basic functions of a service """

        # Creates a service
        service = Service()
        assert service is not None

        # Runs it to see if everything is ok
        service.setup()

    # end test_base_service()

# end class TestService
