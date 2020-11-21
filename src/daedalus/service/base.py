#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Base Class for a Service """

# Standard imports
import inspect
import logging
from enum import Enum
from functools import wraps
import pprint
import os
import signal
import sys
import time
import threading
from typing import Dict, Callable

# Third party imports
from apscheduler.schedulers.background import BackgroundScheduler
import attr
from flask import Flask, jsonify, request
from waitress import serve

# Application imports
from ..workflow.util import get_callable_parent
from ..utility.meta import (
    get_callable_name,
    get_callable_parent,
    get_inner_func
)

logger = logging.getLogger(__name__)


class State(Enum):

    # When the Service was first created
    CREATED = 1

    # Status as it sets up its internal status
    INITIALIZING = 2

    # After initialization and before
    # it is being runned
    READY = 3

    # When the serice goes into its main event loop
    ACTIVE = 4

    # Pausing the event loop. Doesn't actually
    # stops the process.
    INACTIVE = 5

    # When the service has received a terminate
    # signal and requires cleaning up.
    TERMINATING = 6

    # Stopped Service.
    STOPPED = 7


def add_job(name: str = None):
    """ Wrapper function to add job to the class job registry.
    
    If this decorator is used in the class, the class
    object have yet been created. Thus it is stored in
    a cache object that is specific to the module. 
   
    """

    def _inner_decorator(func):
        """ Inner decorator that takes in the function. """

        # Registers the job into a cache that is associated with
        # the module
        job_name = name or get_callable_name(func)
        parent_name, _ = get_callable_parent(func)
        if parent_name:
            mod = inspect.getmodule(get_inner_func(func))
            service_cache = getattr(
                mod,
                "_service_cache",
                dict()
            )
            mod._service_cache = service_cache            
        else:
            raise Exception(f"Fail to register job: {func}")
        if parent_name not in service_cache:
            service_cache[parent_name] = {
                'jobs': {},
                'handlers': {}
            }
        service_cache[parent_name]['jobs'][name] = func

        @wraps(func)
        def wrapped(*args, **kwargs):
            """ Calls the function as per normal """
            return func(*args, **kwargs)
        return wrapped

    return _inner_decorator

# end add_job()

def add_handler():
    """ Wrapper function to add listening end point """
# end add_handler()


class ServiceMeta(type):
    """ Meta class for service """

    def __new__(cls, name, bases, attr):
        """ Constructor """

        service_class = type.__new__(cls, name, bases, attr)

        # Gets the cache from the module
        mod = inspect.getmodule(service_class)
        qualname = service_class.__qualname__

        return service_class

    # end __new__()

# end class ServiceMeta

class Service(metaclass=ServiceMeta):
    """ Base class of a Service """
    
    _job_registry: Dict[str, Callable] = {}
    """ The internal registry of jobs to run """

    _handler_registry: Dict[str, Callable] = {}
    """ Internal registry of handlers for endpoint """

    def __init__(self, name: str = None):
        """ Constructor """

        self._name = name or self.__class__.__name__

        # Default life cycle is CREATED
        self._state = State.CREATED
        
        # The default scheduler is a background scheduler
        self._event_loop = BackgroundScheduler(daemon=True)

        # Name for the end point listener
        self._app = Flask(self._name)

        # Event to wait for exit
        self._quit = threading.Event()

    # end __init__()

    def setup(self):
        """ Setting up the required data before running it """

        # Adds status into the standard endpoint
        self._app.add_url_rule(
            rule='/status',
            endpoint='status',
            view_func=self.status
        )
        self._app.add_url_rule(
            rule='/shutdown',
            endpoint='shutdown',
            view_func=self.shutdown
        )

        # Adds the main function into the event loop
        self._event_loop.add_job(self._app.run, id='endpoint')
        self._event_loop.add_job(self.main, id='main')

    # end setup()

    def run(self):
        """ This is the main function to override for a service """

        try:
            logger.info('Running %s', self._name)
            self._event_loop.start()
            self._quit.wait()
        except KeyboardInterrupt:
            logger.info('Captured Keyboard Interrupt')

        # Exit code, shuts down the event loop and
        # sends a kill signal to stop all the threads
        # This is temporary as we still need to go into
        # TERMINATING state so as to aid with the
        # cleaning up, but the final step is always
        # to send a kill signal.
        time.sleep(1)
        self._event_loop.shutdown(wait=False)
        os.kill(os.getpid(), signal.SIGUSR1)

    # end run()

    def main(self) -> None:
        """ Main function to override """
        
        # Sample code to go into and
        # endless loop
        while True:
            for i in range(5):
                logger.info('Sleeping %s', i)
                time.sleep(1)

        self._quit.set()

    # end main()

    def status(self):
        """ Returns all the information of this service """
        response = {
            'name': str(self._name),
            'state': str(self._state)
        }
        return jsonify(response)

    # end status()

    def shutdown(self):
        """ Calls to shutdown the service """

        # Sets the exit flag
        self._quit.set()

        # Sends a confirmation message
        response = {'message':'Quit event sent'}
        return jsonify(response)

    # end shutdown()

# end class Service
