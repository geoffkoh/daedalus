#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Test module for Service """

# Application imports
from daedalus.service.base import Service

def test_base_service():
    """ Tests the basic functions of a service """

    # Creates a service
    service = Service()
    assert service is not None

    # Runs it to see if everything is ok
    service.setup()
    service.run()

# end test_base_service()
