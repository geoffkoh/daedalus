#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module for creating daemon processes.
"""

# Standard imports
import atexit
import fcntl
import logging
import os
import pwd
import resource
import signal
import sys
from functools import lru_cache

# Third party imports
import psutil

logger = logging.getLogger(__name__)  # pylint: disable=C0103


class DaemonError(Exception):
    """ Generic class for any Daemon related errors """
# end class DaemonError


class Daemon:  # pylint: disable=R0902
    """ Class that implements a Daemon process.

    As per the PEP-3143 standards, a daemon should perform the following steps

    * Close all open file descriptors
    * Change current working directory
    * Reset the file creation mask
    * Run in the background
    * Dissociate from the process group
    * Ignore terminal I/O signals
    * Dissociate from control terminal
    * Don't reacquire control terminal
    * Correctly handle the following circumstances:
        * Started by the System V init process
        * Daemon termination by SIGTERM signal
        * Children generate SIGCHLD signal

    This class attempt to satisfy most of these features.

    Args:
        pid_filename (str): The filename for the pid file. If None is given,
            then the daemon does not create a lockfile.
        stdin (file object or str): The input stream or a filename.
        stdout (file object or str): The output stream or a filename.
        stderr (file object or str): The error stream or a filename.
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

    def __init__(self,  # pylint: disable=R0913
                 pid_filename=None,
                 stdin=None,
                 stdout=None,
                 stderr=None,
                 exclude_list=None,
                 workdir='/',
                 rootdir=None,
                 umask=0o027,  # Default mask level
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
    def is_daemon(self):  # pragma: no cover
        """ Property for _is_daemon. """
        return self._is_daemon
    # end is_daemon()

    @property
    def prevent_core(self):  # pragma: no cover
        """ Property for _prevent_core. """
        return self._prevent_core
    # end prevent_core()

    @property
    def detach_process(self):  # pragma: no cover
        """ Property for _detach_process. """
        return self._detach_process
    # end detach_process()

    def start(self):  # pragma: no cover
        """ Starts the daemonization process. """

        # Does nothing if it is already daemonized
        if self.is_daemon:
            return

        # Changes the current working and root directory
        if self._rootdir:
            change_root_directory(self._rootdir)
        if self._workdir:
            change_working_directory(self._workdir)

        # Reset file creation mask
        change_file_creation(self._umask)

        # Changes the process owner
        change_process_owner(self._uid, self._gid, self._initgroups)

        # Checks if core dump is to be created
        if self.prevent_core:
            prevent_core_dump()

        # Detaches from the parent process if it is required
        # and if this process is not started by init
        if self.detach_process and not is_started_by_init():
            logger.debug('Detaching process')
            detach()

        # Creates the exclude list for file handler closing
        exclude_descriptor_list = self._generate_exclude_file_descriptors()

        # Close all open files
        logger.debug('Closing file descriptors except %s', exclude_descriptor_list)
        close_all_open_files(exclude_descriptor_list)

        # Generates the lock file.
        # logger.debug('Generating lockfile')
        lockfile = generate_lockfile(self._pid_filename)
        try:
            if lockfile:
                lockfile.write(f'{os.getpid()}')
                lockfile.flush()
        except IOError:
            sys.exit(1)

        # Redirects the default stream
        stdin = convert_fileobj(self._stdin, 'r')
        stdout = convert_fileobj(self._stdout, 'a+')
        stderr = convert_fileobj(self._stderr, 'a+')
        redirect_stream(sys.stdin, stdin)
        redirect_stream(sys.stdout, stdout)
        redirect_stream(sys.stderr, stderr)

        # Registers the terminate signal and close event
        # the rest ignore.
        atexit.register(self._close)
        signal.signal(signal.SIGTERM, terminate)

        # Sets the is_daemon flag to true
        self._is_daemon = True
        logger.debug('Daemon started %s', os.getpid())

    # end start()

    def _generate_exclude_file_descriptors(self):
        """ Generates the set of file descriptors to exclude from closing.

        The original exclude list can either contain file descriptors, or
        streams. In this method, we will pass through every item in the
        exclude list and attempts to get the file descriptor if it is
        available.

        Returns:
            A list of file descriptors to be excluded from closing.
        """

        # Builds the exclude list
        exclude_list = []
        exclude_list.extend(self._exclude_list)

        # Adds in the standard streams
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

        return list(exclude_descriptor_list)

    # end _get_exclude_file_descriptors()

    def _close(self):
        """ Closes the daemon.

        The actions that follow the closing of the daemon is to remove the pid file.
        """

        if self._pid_filename and os.path.isfile(self._pid_filename):
            os.remove(self._pid_filename)
        sys.exit(0)

    # end _close()

# end class Daemon


def generate_lockfile(filename):
    """ Generates the lock file on a given filename.

    Args:
        filename (str): The filename to generate lock on.

    Returns:
        A file object, which is the lock file.
    """

    # Returns None if the pid_filename is not specified
    if not filename:
        return None

    # If a lockfile already exists, read it to get the pid
    # that is running
    contents = None
    if os.path.isfile(filename):
        with open(filename, 'r') as file:
            contents = file.read()

    # Creates a lockfile so that only one instance of this daemon is running
    try:
        lockfile = open(filename, 'w')
    except IOError:
        logger.error('Unable to create file %s for generating lock', filename)
        sys.exit(1)

    # Tries to get a lock on the pid file. If fail
    # and if old_pid has some values, rewrite back into
    # the lockfile and exits.
    try:
        fcntl.flock(lockfile, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except IOError:
        logger.error('Unable to lock on %s', filename)
        if contents:  # pragma: no cover
            with open(filename, 'w') as file:
                file.write(contents)
        sys.exit(1)

    # Returns the lockfile
    return lockfile

# end generate_lock()


@lru_cache(maxsize=32)
def convert_fileobj(obj, mode='r'):
    """ Takes in an object and opens it, returning the descriptor.

    This method is used to guess and create the file object and then
    returns its file descriptor.

    If the object is a string, then it assumes it is a file and attempts
    to open it, given the mode.

    If the object is '/dev/null', then it creates a devnull stream.

    If the object has a fileno() function associated with it, then
    it just calls the fileno object.

    Args:
        obj (str or file object): Either a filename or a file object.
        mode (str): The mode for opening the file.

    Returns:
        A file object.

    Raises:
        If we are unable to convert the object into any recognizable
        file object, raise a ``DaemonError`` exception.
    """

    try:
        if obj is None or obj == '/dev/null':
            return None
        elif isinstance(obj, str):
            return open(obj, mode)
        elif hasattr(obj, 'fileno'):
            return obj
        else:
            return None
    except FileNotFoundError:
        raise DaemonError(f'Unable to open {str(obj)}.')

# end convert_fileobj()


def get_file_descriptor(obj):
    """ From the object, gets the file descriptor.

    The file descriptor is an int object. For the input ``obj``, if it is an
    object with ``fileno()`` function, then we attempt to call it and returns
    the result. If it is an ``int``, then we assume it is already a descriptor
    and returns the number. Otherwise returns a ``None``.

    Args:
        obj (object): A python object.

    Returns:
        Returns the file number if it has one, or ``None`` if it has no
        file number associated with it.
    """

    file_descriptor = None
    if hasattr(obj, 'fileno'):
        try:
            file_descriptor = obj.fileno()
        except ValueError:
            pass
    elif isinstance(obj, int):
        file_descriptor = obj

    return file_descriptor

# end get_file_descriptor()


def detach():  # pragma: no cover
    """ Detaches from the parent process.

    This method uses the double forking approach to detach itself from
    the parent process.

    Within each call to ``detach_and_exit_parent()`` is a call to exit using
    ``os._exit()``. This is because some of the handlers that are duplicated
    in the child process should be closed explicitly by the child.

    Raises:
        ``OSError`` if it fails to ``fork`` or ``exit`` for any reason.

    """

    def detach_and_exit_parent(message):
        """ Inner function to detach and exit from parent process """
        try:
            pid = os.fork()
            if pid > 0:
                os._exit(0)  # pylint: disable=W0212
        except OSError:
            # Re-raise the error with more error messages
            raise OSError(f'{message}')

    detach_and_exit_parent('Error in first fork')
    os.setsid()
    detach_and_exit_parent('Error in second fork')

# end detach()


def terminate(signal_number, stack):
    """ Signal handler for terminate

    Args:
        signal_number (int): Integer for describing the signal number.
        stack:

    Raises:
        Terminates by raising a ``SystemExit`` exception.
    """

    logger.debug(stack)
    exception = SystemExit(f'Terminating on signal {signal_number}')
    raise exception

# end terminate()


def redirect_stream(source_stream, target_stream):
    """ Redirect a stream to a specified target stream.

    Redirects a stream from source to target. The source is typically
    the system stdin, stdout, and stderr streams and the target
    would be specified by user. If ``none`` is given for the target, then
    the source stream will be redirected to ``/dev/null``.

    Args:
        source_stream (file obj): The source stream. Must implement ``fileno()``.
        target_stream (file obj): The target stream. Must implement ``fileno()``.
    """

    target_fd = target_stream.fileno() if target_stream \
        else os.open(os.devnull, os.O_RDWR)
    os.dup2(target_fd, source_stream.fileno())

# end redirect_stream()


def close_all_open_files(exclude_descriptor_list=None):
    """ Closes all open files.

    This method gets all open files from the current process and calls them.
    Instead of getting a range of values and trying all of them out, it uses
    the ``psutil`` module of finding open files and uses that instead. This
    way, we will not close any unintended open descriptors.

    Args:
        exclude_descriptor_list (list): List of file descriptors to not close
    """

    exclude_descriptor_list = exclude_descriptor_list or []

    # Gets the current descriptor list
    curr_process = psutil.Process()
    descriptor_list = [entry.fd for entry in curr_process.open_files()]

    # Close them
    for descriptor in descriptor_list:
        if descriptor not in exclude_descriptor_list:
            try:
                os.close(descriptor)
            except OSError:  # pragma: no cover
                pass

# end close_all_open_files()


def change_file_creation(umask):
    """ Changes the file creation mask.

    Args:
        umask (int) : The numeric file creation mask to set.

    Raises:
        Raises a ``DaemonError`` if the umask changing operation fails.

    """

    try:
        logger.debug('Changing file creation mask %s', umask)
        os.umask(umask)
    except Exception as exc:
        message = f'Unable to change file creation mask ({exc})'
        logger.error(message)
        raise DaemonError(message)

# end change_file_creation()


def change_root_directory(path):  # pragma: no cover
    """ Changes the root directory.

    This operation should only be run if one is running the code
    as a root user.

    Args:
        path (str): The root directory to change to.

    Raises:
        Raises a ``DaemonError`` for any reason that causes the
        changing of root directory to fail.
    """

    try:
        logger.debug('Changing root directory to %s', path)
        os.chroot(path)
    except Exception as exc:
        message = f'Unable to change root directory to {path} ({exc})'
        logger.error(message)
        raise DaemonError(message)

# end change_root_directory()


def change_working_directory(workdir):
    """ Changes the current working directory.

    Args:
        workdir (str): The working directory.

    Raises:
        Raises a ``DaemonError`` for any reason that causes the
        changing of working directory to fail.
    """

    try:
        logger.debug('Changing working directory to %s', workdir)
        os.chdir(workdir)
    except Exception as exc:
        message = f'Unable to change working directory to {workdir} ({exc})'
        logger.error(message)
        raise DaemonError(message)

# end change_working_directory()


def change_process_owner(uid, gid, initgroups=False):
    """ Changes the owning uid, gid and groups of this process.

    This method ensures that the daemon being created has the same uid and gid as the
    process that started the daemon.

    Args:
        uid (int): The user id.
        gid (int): The group id.
        initgroups (bool) : Whether to set the supplementary groups to that of the user.

    Raise:
        Raises a ``DaemonError`` if the operation encounters any error.
    """

    username = None
    try:
        username = pwd.getpwuid(uid).pw_name
    except KeyError:
        logger.warning('Cannot find username for %s', uid)
        initgroups = False

    try:
        logger.debug('Setting gid for %s to %s', username, gid)
        if initgroups:  # pragma: no cover
            os.initgroups(username, gid)
        else:
            os.setgid(gid)
        os.setuid(uid)
    except Exception as exc:
        message = f'Unable to change process owner ({exc})'
        logger.error(message)
        raise DaemonError(message)

# end change_process_owner()


def prevent_core_dump():
    """ Prevents process from generating a core dump

    This method checks if the current environment supports core dump.
    If it does, then it sets the core dump limits to 0, i.e. prevent
    core dumping.

    This is to prevent any failure of daemon operation to expose any
    sensitive data.

    Raises:
        Raises a ``ValueError`` with additional warnings.
    """

    core_resource = resource.RLIMIT_CORE
    try:
        resource.getrlimit(core_resource)
    except ValueError:
        logger.warning('System does not support RLIMIT_CORE resource limit')
        raise

    core_limit = (0, 0)
    resource.setrlimit(core_resource, core_limit)

# end prevent_core_dump()


def is_started_by_init():
    """ Checks if this process is started by init.

    If a process is started by the init process, then the parent id will be 1.
    If so it will return a ``True``. Otherwise this method will return ``False.

    Returns:
        A boolean whether or not the process is started by init.
    """

    if os.getppid() == 1:
        return True

    return False

# end is_init_process()
