#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Standard imports
import logging
import multiprocessing as mp
import sys
import time
import tempfile
import os
import signal
import resource
import io

# Third party imports
import unittest
from unittest import mock
import psutil

# Application imports
import daedalus.process.daemon as daemon

logger = logging.getLogger(__name__)


class TestDaemon(unittest.TestCase):
    """ Test class for the daemon. """

    def test_create(self):
        """ Tests the create function. """

        my_daemon = daemon.Daemon()
        assert my_daemon is not None, 'The daemon should be created'

    # end test_create()

    def test_start(self):
        """ Tests the starting of the daemon process """

        # Creates a temporary dir to hold the pid file.
        temp_dir = tempfile.TemporaryDirectory()
        pid_filename = os.path.join(temp_dir.name, 'pid.txt')

        def work():
            """ Inner function to do the work """

            # Do not close the standard streams
            my_daemon = daemon.Daemon(pid_filename=pid_filename,
                                      stdin=sys.stdin,
                                      stdout=sys.stdout,
                                      stderr=sys.stderr)
            my_daemon.start()
            time.sleep(20)
        # end work()

        # Creates a daemon process and runs it
        daemon_process = mp.Process(target=work)
        daemon_process.start()

        # Wait until pid file exists
        time.sleep(1)
        assert os.path.isfile(pid_filename), f'The pid file {pid_filename} should be created'

        # Checks that the pid file exists
        with open(pid_filename) as file:
            pid = int(file.read())
            assert psutil.pid_exists(pid), f'The daemon process with pid {pid} does not exist'

            # Kills the daemon
            os.kill(pid, signal.SIGTERM)
            time.sleep(1)
            assert not psutil.pid_exists(pid), f'The daemon process should not exist'

            # We cannot test the atexit function here as multiprocess is killed
            # via os._exit, in which atexit() function won't be called.

    # end test_start()

    def test_generate_exclude_file_descriptors(self):
        """ Tests the function to generate exclude fd. """

        # Case 1: Normal daemon with system streams
        my_daemon = daemon.Daemon(stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr)
        exclude_list = my_daemon._generate_exclude_file_descriptors()
        assert len(exclude_list) > 0, 'The exclude list should include system streams'

        # Case 2: Daemon with exclude lists
        temp_file = tempfile.NamedTemporaryFile()
        my_daemon = daemon.Daemon(stdin=sys.stdin,
                                  stdout=sys.stdout,
                                  stderr=sys.stderr,
                                  exclude_list=[temp_file, None, '/does/not/exist'])
        exclude_list = my_daemon._generate_exclude_file_descriptors()
        assert temp_file.fileno() in exclude_list, 'The temp file should be in the exclude list'
        assert None not in exclude_list, 'None should not be in the exclude list'

    # end test_generate_exclude_file_descriptors()

    def test_close(self):
        """ Tests the closing of a daemon"""

        # Case 1: Normal daemon with pid file
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        my_daemon = daemon.Daemon(pid_filename=temp_file.name)

        with mock.patch('sys.exit') as mock_exit:
            my_daemon._close()
            assert mock_exit.called, 'Exit should be called'
            assert not os.path.isfile(temp_file.name), 'PID file should be removed'

        # Case 2: Daemon without a pid file
        my_daemon = daemon.Daemon()
        with mock.patch('sys.exit') as mock_exit:
            my_daemon._close()
            assert mock_exit.called, 'Exit should be called'

    # end test_close()

# end class TestDaemon


class TestDaemonMethods(unittest.TestCase):
    """ Class to test module functions. """

    def test_generate_lockfile(self):
        """ Tests the creation of lockfile. """

        # Case 1: Tests if pass in None
        lock = daemon.generate_lockfile(None)
        assert lock is None, 'The lockfile for None should be None'

        # Case 2: Tests if a lockfile exists and one cannot obtain lock
        with mock.patch('sys.exit') as mock_exit:
            with mock.patch('fcntl.flock') as mock_flock:

                # Mocks the functions
                mock_exit.return_value = 0
                mock_flock.side_effect = IOError()

                temp_lockfile = tempfile.NamedTemporaryFile('w')
                temp_lockfile.write('old contents')
                temp_lockfile.flush()
                daemon.generate_lockfile(temp_lockfile.name)

                with open(temp_lockfile.name) as file:
                    contents = file.read()
                    assert contents == 'old contents'

        # Case 3: Normal case with unused lock file
        temp_lockfile = tempfile.NamedTemporaryFile('w')
        daemon.generate_lockfile(temp_lockfile.name)
        with open(temp_lockfile.name) as file:
            contents = file.read()
            assert contents == '', 'The lockfile should be empty'

        # Case 4: Normal case with new lock file
        temp_dir = tempfile.TemporaryDirectory()
        temp_lockfilename = os.path.join(temp_dir.name, 'lock.txt')
        daemon.generate_lockfile(temp_lockfilename)
        with open(temp_lockfilename) as file:
            contents = file.read()
            assert contents == '', 'The lockfile should be empty'

        # Case 5: Totally invalid filename
        with mock.patch('sys.exit') as mock_exit:
            mock_exit.side_effect = SystemExit  # Replace with SystemExit
            try:
                daemon.generate_lockfile('does/not/exists')
            except SystemExit:
                assert mock_exit.called, 'The exit is called'

    # end test_generate_lockfile()

    def test_change_root_directory(self):
        """ Tests the change root directory function """

        # Case 1: Just checking to see if the proper error is raised
        invalid_root = 'does_not_exist'
        try:
            daemon.change_root_directory(invalid_root)
            assert False, 'Should not reach this part'
        except daemon.DaemonError as exc:
            assert isinstance(exc, daemon.DaemonError)
            assert True, 'Should catch an error when changing root to invalid path'

    # end test_change_root_directory()

    def test_terminate(self):
        """ Tests the terminate function """

        try:
            daemon.terminate(signal.SIGTERM, None)
            assert False, 'A SystemExit exception is not raised'
        except SystemExit:
            assert True, 'SystemExit should be raised'

    # end test_terminate()

    def test_redirect_stream(self):
        """ Tests the redirect stream function """

        source_stream = tempfile.NamedTemporaryFile('w')
        target_stream = tempfile.NamedTemporaryFile('w')
        logger.debug(f'Creating source stream with name {source_stream.name}')
        logger.debug(f'Creating target stream with name {target_stream.name}')

        original_string = 'hello world'

        # Case 1: Redirects source stream to target stream
        daemon.redirect_stream(source_stream, target_stream)

        # Tests by writing something to source stream
        source_stream.write(original_string)
        source_stream.flush()

        # Checks that target stream has it
        with open(target_stream.name, 'r') as file:
            contents = file.read()
            assert contents == original_string, 'The stream would be redirected'

        # Case 2: Redirect to /dev/null
        daemon.redirect_stream(source_stream, None)

        # Writes some more to the source string
        source_stream.write(original_string)
        source_stream.flush()

        # Checks that the target stream is still the original content
        with open(target_stream.name, 'r') as file:
            contents = file.read()
            assert contents == original_string, 'The target stream should not be changed'

    # end test_redirect_stream()

    def test_get_file_descriptor(self):
        """ Tests the function ``_get_file_descriptor()``. """

        # Tests getting from non int and no fileno
        io_stream = io.StringIO()
        descriptor = daemon.get_file_descriptor(io_stream)
        assert descriptor is None, 'Should return a None for obj with no fileno()'
        descriptor = daemon.get_file_descriptor('invalid')
        assert descriptor is None, 'Should return a None for string'

        # Tests getting a fileno from a normal file object
        temp_file = tempfile.NamedTemporaryFile('w')
        descriptor = daemon.get_file_descriptor(temp_file)
        assert isinstance(descriptor, int), 'The obj should have an int file descriptor.'

        # Tests on passing in an integer
        input_descriptor = 1
        descriptor = daemon.get_file_descriptor(input_descriptor)
        assert descriptor == input_descriptor, 'The descriptor should be the same'

    # end test_get_file_descriptor()

    def test_close_all_open_files(self):
        """ Tests the function that closes all open files """

        # Creates an open file
        temp_file = tempfile.NamedTemporaryFile('w')
        temp_file_exclude = tempfile.NamedTemporaryFile('w')

        # Asserts that the file is open
        assert not temp_file.closed, 'The temp file should be open'

        # Attempts to close it except for sys streams
        exclude_list = [daemon.get_file_descriptor(stream)
                        for stream in [sys.stdin,
                                       sys.stdout,
                                       sys.stderr,
                                       temp_file_exclude]]
        daemon.close_all_open_files(exclude_descriptor_list=exclude_list)

        try:
            temp_file.close()
            assert False, 'Should not reach this line'
        except OSError:
            assert True, 'Closing the file should give an error'

        try:
            temp_file_exclude.close()
            assert True, 'Should be able to close the file'
        except OSError:
            assert False, 'Should not throw an error'

    # end test_close_all_open_files()

    def test_change_file_creation(self):
        """ Tests the changing of file creation mask """

        # Gets current umask
        def get_curr_umask():
            curr_umask = os.umask(0)
            os.umask(curr_umask)
            return curr_umask

        # Sets the umask to 0o027
        original_umask = get_curr_umask()
        daemon.change_file_creation(0o027)
        new_umask = get_curr_umask()
        assert new_umask == 0o027, 'The umask should be changed'

        # Change back
        daemon.change_file_creation(original_umask)

        # Tests invalid umask
        try:
            daemon.change_file_creation('invalid')
            assert False, 'Should not reach this line'
        except daemon.DaemonError:
            assert True, 'The exception is caught'

    # end test_change_file_creation()

    def test_change_working_directory(self):
        """ Tests the changing of working directory """

        # Case 1: Normal change

        # Gets the current working directory
        original_dir = os.getcwd()
        temp_dir = tempfile.TemporaryDirectory()
        daemon.change_working_directory(temp_dir.name)
        assert os.path.realpath(os.getcwd()) == os.path.realpath(temp_dir.name), \
            'The working directory should be changed.'

        # Change back working directory
        os.chdir(original_dir)

        # Does a clean up
        temp_dir.cleanup()

        # Case 2: Invalid path
        try:
            invalid_path = '/does/not/exist'
            daemon.change_working_directory(invalid_path)
            assert False, 'Should not reach this line'
        except daemon.DaemonError:
            assert True, 'The exception is caught'

    # end test_change_working_directory()

    def test_change_process_owner(self):
        """ Tests the changing of the process owner """

        # Change to this uid and gid
        try:
            uid = os.getuid()
            gid = os.getgid()
            daemon.change_process_owner(uid, gid)
            assert True, 'Changing process owners without errors'
        except daemon.DaemonError:
            assert False, 'Should not reach this line'

        # Case 2: Invalid uid and gid
        try:
            daemon.change_process_owner(-999, -999)
            assert False, 'Should not reach this line'
        except daemon.DaemonError:
            assert True, 'The exception should be caught'

    # end test_change_process_owner()

    def test_prevent_core_dump(self):
        """ Test the option to prevent core dump """

        # Call prevent core dump
        daemon.prevent_core_dump()

        # Checks to make sure the limit is 0
        core_resource = resource.RLIMIT_CORE
        limit = resource.getrlimit(core_resource)

        assert limit == (0, 0), 'The resource limit for core dump should be (0, 0).'

        # Mocks the case whereby it does not support RLIMIT_CORE
        with mock.patch('resource.getrlimit') as mock_getrlimit:
            mock_getrlimit.side_effect = ValueError
            try:
                daemon.prevent_core_dump()
                assert False, 'Should not reach this line'
            except ValueError:
                assert True, 'The exception should be caught'

    # end test_prevent_core_dump()

    def test_is_started_by_init(self):
        """ Tests if this process is started by init """

        # Normal case
        assert not daemon.is_started_by_init(), 'The default should not be started by init'

        # Mock case where process is started by init
        with mock.patch('os.getppid') as mock_getppid:
            mock_getppid.return_value = 1
            assert daemon.is_started_by_init(), 'The process should be started by init'

    # end test_is_started_by_init()

    def test_convert_fileobj(self):
        """ Tests the function convert_fileobj() """

        # Case 1: Tests for None and /dev/null
        devnull_file = daemon.convert_fileobj('/dev/null')
        none_file = daemon.convert_fileobj(None)

        assert none_file == devnull_file, 'Should have the same /dev/null object'
        assert none_file is None, 'The return value should be None'

        # Case 2: Tests for normal stream
        stdout_file = daemon.convert_fileobj(sys.stdout)
        assert stdout_file == sys.stdout, 'The original object should pass through.'

        # Case 3: Pass in a filename
        temp_dir = tempfile.TemporaryDirectory()
        temp_file = os.path.join(temp_dir.name, 'temp.txt')
        file = daemon.convert_fileobj(temp_file, 'w')
        file.write('hello world')
        file.close()

        # Tries reading it again
        with open(temp_file, 'r') as input_file:
            contents = input_file.read()
            assert contents == 'hello world'

        # Case 4: Invalid input
        try:
            daemon.convert_fileobj('/path/does/not/exist')
            assert False, 'Should not reach here'
        except daemon.DaemonError:
            assert True, 'Exception is caught.'

        # Case 5: Taking in an int
        file = daemon.convert_fileobj(1)
        assert file is None, 'The return file should be a None'

    # end test_convert_fileobj()

# end class TestDaemonMethods
