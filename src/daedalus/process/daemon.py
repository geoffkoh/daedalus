#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Standard imports
import atexit
import fcntl
import logging
import os
import pwd
import resource
import signal
import sys

# Third party imports

# Application imports

logger = logging.getLogger(__name__)


class Daemon:
    """ Class that implements a Daemon process.

    Args:
        pid_filename (str): The filename for the pid file. If None is given, then the daemon does not create a lockfile.
        stdin (file object): The input stream.
        stdout (file object): The output stream.
        stderr (file object): The error stream.
        exclude_list (list): List of file descriptors or file objects that should not be closed.
        workdir (str) : The working directory of the daemon.
        rootdir (str) : The root directory of the process
        umask (int) : File access creation mask to set for the process on daemon start.
        detach_process (bool) : Flag to determine whether or not to determine this process.
        uid (int) : user id. Default is ``os.getuid()``.
        gid (int) : user group id. Default is ``os.getgid()``.
        initgroups (bool) : If true, set the daemon's process supplementary groups to the given uid.
        prevent_core (bool) : If true, prevents the generation of core files.
    """

    def __init__(self,
                 pid_filename=None,
                 stdin=None,
                 stdout=None,
                 stderr=None,
                 exclude_list=None,
                 workdir='/',
                 rootdir=None,
                 umask=0,
                 uid=None,
                 gid=None,
                 initgroups=False,
                 prevent_core=True,
                 detach_process=True):
        """ Constructor """

        self._pid_filename = os.path.abspath(pid_filename) if pid_filename else None
        self._stdin = stdin
        self._stdout = stdout
        self._stderr = stderr
        self._exclude_list = exclude_list or []  # list of file descriptors to keep open
        self._workdir = workdir
        self._rootdir = rootdir
        self._umask = umask
        self._uid = uid if uid else os.getuid()
        self._gid = gid if gid else os.getgid()
        self._initgroups = initgroups
        self._prevent_core = prevent_core
        self._detach_process = detach_process

        # Flag to indicate if the process is already daemonize
        self._is_daemon = False

    # end __init__()

    @property
    def is_daemon(self):
        return self._is_daemon
    # end is_daemon()

    @property
    def prevent_core(self):
        return self._prevent_core
    # end prevent_core()

    @property
    def detach_process(self):
        return self._detach_process
    # end detach_process()

    def start(self):
        """ Starts the daemonization process """

        # Does nothing if it is already daemonized
        if self.is_daemon:
            return

        # Changes the root directory
        if self._rootdir:
            change_root_directory(self._rootdir)

        # Changes the process owner and working dir
        change_file_creation(self._umask)
        change_working_directory(self._workdir)
        change_process_owner(self._uid, self._gid, self._initgroups)

        # Checks if core dump is to be created
        if self.prevent_core:
            prevent_core_dump()

        # Detaches from the parent process
        if self.detach_process:
            self.detach()

        # Adds the normal streams into the exclude list
        exclude_descriptor_list = self._generate_exclude_file_descriptors()

        # Close all open files
        close_all_open_files(exclude_descriptor_list)

        # Generates the lock file. This one is placed after
        # all other open files are closed
        lockfile = self.generate_lockfile()
        try:
            if lockfile:
                lockfile.write(f'{os.getpid()}')
                lockfile.flush()
        except IOError:
            sys.exit(1)

        # Redirects the default stream
        redirect_stream(self._stdin, sys.stdin)
        redirect_stream(self._stdout, sys.stdout)
        redirect_stream(self._stderr, sys.stderr)

        # Registers the terminate signal and close event
        signal.signal(signal.SIGTERM, self.terminate)
        atexit.register(self.close)

        # Sets the is_daemon flag to true
        self._is_daemon = True

        logger.debug('Daemon created')

    # end start()

    def generate_lockfile(self):
        """ Generates the lock file """

        # Returns None if the pid_filename is not specified
        if not self._pid_filename:
            return None

        # If a lockfile already exists, read it to get the pid
        # that is running
        old_pid = None
        if os.path.isfile(self._pid_filename):
            with open(self._pid_filename, 'r') as pidfile:
                old_pid = pidfile.read()

        # Creates a lockfile so that only one instance of this daemon is running
        try:
            lockfile = open(self._pid_filename, 'w')
        except IOError:
            logger.error('Unable to create pid file')
            sys.exit(1)

        # Tries to get a lock on the pid file. If fail
        # and if old_pid has some values, rewrite back into
        # the lockfile and exits.
        try:
            fcntl.flock(lockfile, fcntl.LOCK_EX|fcntl.LOCK_NB)
        except IOError:
            logger.error('Unable to lock on pidfile')
            if old_pid:
                with open(self._pid_filename, 'w') as pidfile:
                    pidfile.write(old_pid)
            sys.exit(1)

        # Returns the lockfile
        return lockfile

    # end generate_lock()

    def detach(self):
        """ Detaches from the parent process """

        def detach_and_exit_parent():
            try:
                pid = os.fork()
                if pid > 0:
                    os._exit(0)
            except OSError as e:
                raise e

        detach_and_exit_parent()
        os.setsid()
        detach_and_exit_parent()

    # end detach()

    def terminate(self, signal_number):
        """ Signal handler for terminate """

        exception = SystemExit(f'Terminating on signal {signal_number}')
        raise exception

    # end terminate()

    def close(self):
        """ Closes the daemon """

        if self._pid_filename:
            os.remove(self._pid_filename)
        sys.exit(0)

    # end close()

    def _generate_exclude_file_descriptors(self, exclude_list=None):
        """ Generates the set of file descriptors to exclude from closing """

        # Builds the exclude list
        exclude_list = exclude_list or []
        exclude_list.extend(self._exclude_list)
        exclude_list.extend([self._stdin, self._stdout, self._stderr])

        # This is the list of all descriptors
        exclude_descriptor_list = set()

        # Goes through each individual item in the exclude list
        for item in exclude_list:
            if item is None:
                continue
            descriptor = get_file_descriptor(item)
            if descriptor is not None:
                exclude_descriptor_list.add(descriptor)
            else:
                exclude_descriptor_list.add(item)

        return exclude_descriptor_list

    # end _get_exclude_file_descriptors()

# end class Daemon


def redirect_stream(source_stream, target_stream):
    """ Function to redirect a stream to a specified file

    Args:
        source_stream ():
        target_stream ():
    """

    if target_stream is None:
        target_fd = os.open(os.devnull, os.O_RDWR)
    else:
        target_fd = target_stream.fileno()
    os.dup2(source_stream.fileno(), target_fd)

# end redirect_stream()


def close_all_open_files(exclude_descriptor_list=None):
    """ Closes all open files.

    This method gets the soft limits of the open files and tries to
    close them.

    Args:
        exclude_descriptor_list (list): List of file descriptors to not close
    """

    for descriptor in range(resource.getrlimit(resource.RLIMIT_NOFILE)[0]):
        if descriptor not in exclude_descriptor_list:
            try:
                os.close(descriptor)
            except OSError:
                pass

# end close_all_open_files()


def change_file_creation(umask):
    """ Changes the file creation mask.

    Args:
        umask (int) : The numeric file creation mask to set.

    """

    try:
        os.umask(umask)
    except Exception as e:
        logger.error(f'Unable to change file creation mask ({e})')
        raise e

# end change_file_creation()


def change_root_directory(rootdir):
    """ Changes the root directory """

    try:
        os.chroot(rootdir)
    except Exception as e:
        logger.error(f'Unable to change root directory ({e})')
        raise e

# end change_root_directory()


def change_working_directory(workdir):
    """ Changes the current working directory

    Args:
        workdir (str): The working directory

    """

    try:
        os.chdir(workdir)
    except Exception as e:
        logger.error(f'Unable to change working directory ({e})')
        raise e

# end change_working_directory()

def change_process_owner(uid, gid, initgroups=False):
    """ Changes the owning uid, gid and groups of this process.

    Args:
        uid (int): The user id.
        gid (int): The group id.
        initgroups (bool) : Whether to set the supplementary groups to that of the user.

    """

    try:
        username = pwd.getpwuid(uid)
    except KeyError:
        logger.warning(f'Cannot find username for {uid}')
        initgroups = False

    try:
        if initgroups:
            os.initgroups(username, gid)
        else:
            os.setgid(gid)
        os.setuid(uid)
    except Exception as e:
        logger.error(f'Unable to change process owner ({e})')
        raise e

# end change_process_owner()


def prevent_core_dump():
    """ Prevents process from generating a core dump

    This method checks if the current environment supports core dump.
    If it does, then it sets the core dump limits to 0, i.e. prevent
    core dumping.
    """

    core_resource = resource.RLIMIT_CORE
    try:
        resource.getrlimit(core_resource)
    except ValueError:
        logger.warning('System does not support RLIMIT_CORE resource limit')
        return

    core_limit = (0,0)
    resource.setrlimit(core_resource, core_limit)

# end prevent_core_dump()


def get_file_descriptor(obj):
    """ From the object, gets the file descriptor """

    file_descriptor = None
    if hasattr(obj, 'fileno'):
        try:
            file_descriptor = obj.fileno()
        except ValueError:
            pass

    return file_descriptor

# end get_file_descriptor()
