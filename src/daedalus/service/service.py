#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module for specifying services

Everybody starts off with the definition of Microservice as a Flask or Web based application, i.e.
something that stays running and only respond to messages that gets routed to their respective handlers.

Requirements of a service:

* It should have a life-cycle
* It should have a scheduler/event loop which we can schedule tasks to it.
* A service base should never be used as a standalone; it should be subclassed by others and \
    any additional features implemented via the use of mixins.


Scheduler
=========
The scheduler should run in a separate Thread from the main flask application.

"""

# Standard imports
from functools import partial
import logging

# Third party imports
from flask import Flask, request
from apscheduler.schedulers.background import BackgroundScheduler

# Application imports

logger = logging.getLogger(__name__)

ROUTE_MAP = {}
SCHEDULE_MAP = {}


def route(rule, **options):

    def inner(func):
        ROUTE_MAP[rule] = {'func': func, 'options': options}
        return func
    return inner



class ServiceBase:
    """ This is the base class for a service """

    app = None

    def __init__(self):
        """ Constructor """

        # Creates the Flask application and registers all the routes
        self.app = Flask(__name__)
        for rule, func_dict in ROUTE_MAP.items():
            func = func_dict['func']
            options = func_dict['options']
            partial_func = partial(func, self)
            partial_func.__name__ = func.__name__
            self.app.route(rule, **options)(partial_func)

        self.scheduler = BackgroundScheduler()

        # Adds a heartbeat every 5 sec
        # self.scheduler.add_job(self.heartbeat, 'interval', seconds=5)

    # end __init__()

    def __del__(self):
        """ Destructor """

        self.scheduler.shutdown()

    # end __del__()

    def start(self):
        """ Function to call to start a service """

        logger.info('Running the internal flask engine')
        self.scheduler.start()
        self.app.run()

    # end start()

    @route('/', methods=['GET', 'POST'])
    def index(self):
        return f'Hello world'
    # end index

    @route('/post', methods=['POST'])
    def post(self):
        """ Testing the post method """

        print('Contents of request')
        print(request.get_json())
        return request.get_json()

    # end post

    def heartbeat(self):
        print('alive')

# end class ServiceBase
