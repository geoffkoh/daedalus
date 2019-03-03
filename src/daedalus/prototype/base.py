#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module for the basic Service class.
"""

# System imports
import logging
import multiprocessing
import time
import sys

# Third party imports

# Application imports
import daedalus.process.daemon as daemon

logger = logging.getLogger(__name__)


class BaseService:
    """ This is the base prototype class """

    def __init__(self, is_daemon=True):
        """ Constructor """

        self._is_daemon = is_daemon

        self._source = []  # List of sources
        self._heartbeat = []  # The list of heartbeat mechanism

        self._status = None  # The initial status of the prototype

        # Items for managing the processes
        self._process_pool = []
        self._context = multiprocessing.Manager().dict()
        self._queue = multiprocessing.JoinableQueue()

    # end __init__()

    def start(self):
        """ Starts the prototype """

        print('I am running now')

        # Checks if it is daemon mode.
        if self._is_daemon:
            logger.info('Starting daemon')
            d = daemon.Daemon(stdout=sys.stdout)
            d.start()

        # Just goes into an endless loop
        while True:
            print('i am sleeping')
            time.sleep(5)

    # end start()

    def initialize(self):
        """ This method will do all the initialization. """
        pass

    # end initialize()

# end class BaseService
