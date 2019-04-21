#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
*******
Summary
*******

Module with the implementation of a service object.

The ``Service`` object comprise of a flask application which will listen to the given port and host
for any external messages and events. Within it will be a main event loop engine which is implemented
as a separate process.

"""

# Standard imports
import sys
import logging
from multiprocessing import Process, Queue, Manager, Value
import time
import ctypes

# Third party imports
from flask import Flask, request
import waitress

# Application imports

logger = logging.getLogger(__name__)

class ServeEngine(Process):

    def __init__(self, context, exit):
        """ Constructor """
        super().__init__()

        self.context = context  # The global context
        self.exit = exit
        self.test_variable = 5

        self.app = Flask(__name__)
        # self.app.add_url_rule('/', 'index', self.index)
        self.app.add_url_rule('/put/<key>/<value>', 'put', self.put)
        self.app.add_url_rule('/quit', 'quit', self.quit)

    # end __init__()

    def run(self):
        """ Start off the process and creates a simple http server """
        waitress.serve(self.app, port=8080)

    def index(self):
        return f'{self.app} This is my test {self.context}.'

    def put(self, key, value):
        self.context[key] = value
        return f'I placed {key} {value} into context'

    def quit(self):
        self.context['quit'] = True
        return 'Exiting...'


# end ServeEngine()

class ConsumeEngine(Process):

    def __init__(self, context, exit):
        """ Constructor """
        super().__init__()
        self.context = context  # The global context
        self.exit = exit
        print(f'[{self.name}] consume process created')

    # end __init__()

    def run(self):
        """ Start off the process and creates a simple http server """
        while True:
            print(f'[{self.name}] Running ... ')
            print(f'{self.context}')
            time.sleep(5)

# end ConsumeEngine()

class Service:
    """ The base class for a single service.

    By itself the service has no capabilities, but it forms the glue to allow different processes
    to communicate with one another, each with its own responsibilities.

    What the ``Service`` parent object does provide is a Queue and dictionary of shared objects.
    """

    def __init__(self):
        """ Constructor """

        self.queue = Queue()
        self.context = Manager().dict()
        self.exit = Value('i', False)

        self.serve_engine = ServeEngine(self.context, self.exit)       # Engine to listen to end points for external communication
        self.consumer_engine = ConsumeEngine(self.context, self.exit)  # Consumer engine to listen to various sources to get events
        self.process_engine = None              # Processor engine to listen to job queue to carry out tasks


    # end __init__()


    def start(self):
        """ Starts the service """

        # Starts off the engines
        processes = [self.serve_engine, self.consumer_engine]
        for p in processes:
            p.start()

        print('Started processes')

        while not self.context.get('quit', False):
            print(f'Main process {self.context.get("quit", False)}')
            time.sleep(1)

        for p in processes:
            p.terminate()

    # end start()

# end class Service


