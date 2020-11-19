#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Sample Service that is made by composition """

# System imports
import logging

# Application imports
from .base import Service

logger = logging.getLogger(__name__)


class SampleService(Service):
    """ A sample service """
# end class SampleService
