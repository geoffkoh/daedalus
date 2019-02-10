#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Standard imports
import logging
import multiprocessing as mp
import sys

# Third party imports
import unittest

# Application imports
import daedalus.process.daemon as daemon

class TestDaemon(unittest.TestCase):

    def test_create(self):

        my_daemon = daemon.Daemon()
        assert my_daemon is not None, 'The daemon should be created'

    # end test_create()

    def test_start(self):
        """ Tests the starting of the daemon process """

        def work():
            print('Just before starting the daemon')
            my_daemon = daemon.Daemon(pid_filename="pid.log", stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr)
            my_daemon.start()
            import time
            time.sleep(30)

        p = mp.Process(target=work)
        p.start()

    # end test_start()

# end class TestDaemon
