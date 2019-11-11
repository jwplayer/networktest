import sys
import traceback
import socket
from enum import Enum, auto

from .pytest.integration import PytestIntegration


class NetworkBlockException(Exception):
    """
        An exception that is raised when a network request is made while using
        NetworkBlocker in STRICT mode.
    """

    def __init__(self):
        return super().__init__(
            'A test that should not be doing so opened a network connection.'
        )


class NetworkBlocker:

    class Modes(Enum):
        """
            Mode settings for use with NetworkBlocker
        """

        STRICT = auto()
        WARNING = auto()
        DISABLED = auto()

    class AllowablePackages:
        """
            Lists of packages that may be permitted to make requests in
            certain situations
        """
        DATASTORE = [
            'sqlalchemy',
            'redis',
            'celery'
        ]

    def __init__(
        self,
        mode: auto = None,
        allowed_packages=None,
        filter_stack: bool = True
    ):
        """
            A context manager that prevents network requests while active.

            The context manager has multiple modes:
            * NetworkBlocker.Modes.STRICT (default) - Raise
                NetworkBlockException when any network requests are attempted
            * NetworkBlocker.Modes.WARNING - Log a warning when any network
                requests are attempted
            * NetworkBlocker.Modes.DISABLED - Do nothing. This is mainly
                useful if you want to temporarily disable NetworkBlocker
                without removing it.

            Recommended configurations for types of tests:
            * Unit tests - NetworkBlocker()
            * Functional tests -
                NetworkBlocker(allowed_packages=NetworkBlocker.AllowablePackages.DATASTORE)

            Args:
                mode (enum.auto): Determines the behavior of NetworkBlocker
                    when a network request is detected.
                allowed_packages (list of strings): List of packages that are
                    allowed to make network requests.
                filter_stack (bool): Whether or not to filter out libraries
                    from the call stack in WARNING mode so it's easier to see
                    exactly where in application a request is made.
        """

        self.mode = self.Modes.STRICT if mode is None else mode
        self.allowed_packages = [] if allowed_packages is None \
            else allowed_packages
        self.filter_stack = filter_stack

    def __enter__(self):
        self.original_socket = socket.socket

        if self.mode != self.Modes.DISABLED:
            socket.socket = self.replacement_socket

    def __exit__(self, type, value, traceback):
        if self.mode != self.Modes.DISABLED:
            socket.socket = self.original_socket

    def stack_allowed(self, stack) -> bool:
        """
            Returns a boolean if a given call stack is allowed to make
                network requests.
            This is determined by checking the packages used
                against allowed_packages.
        """
        return any(
            any(
                '/%s/' % package in frame.filename and
                frame.filename[
                    :frame.filename.find('/%s/' % package)
                ] in sys.path
                for package in self.allowed_packages
            )
            for frame in stack
        )

    def replacement_socket(self, *args, **kwargs):

        stack = traceback.extract_stack()
        if not self.stack_allowed(stack):
            if self.mode == self.Modes.STRICT:
                raise NetworkBlockException()
            elif self.mode == self.Modes.WARNING:
                stop_capture = PytestIntegration.capman and \
                    PytestIntegration.capman.is_globally_capturing()
                if stop_capture:
                    PytestIntegration.capman.suspend_global_capture()

                print(file=sys.stderr)
                print('A test that should not be doing so opened ' +
                      'a network connection.', file=sys.stderr)
                print('This was most likely an API request.', file=sys.stderr)
                print('It happened here:', file=sys.stderr)

                if self.filter_stack:
                    # Ideally this uses a full path (eg. /usr/lib/pythonx.x)
                    #   but how can we get that reliably without
                    #   making assumptions?
                    stack = filter(
                        lambda frame: 'python' not in frame.filename,
                        stack
                    )
                for st in traceback.format_list(stack):
                    print(st, end='', file=sys.stderr)

                if stop_capture:
                    PytestIntegration.capman.resume_global_capture()

        return self.original_socket(*args, **kwargs)


PRESET_KWARGS_BLOCKED = {
    'mode': NetworkBlocker.Modes.STRICT,
}
PRESET_KWARGS_LIMITED = {
    'mode': NetworkBlocker.Modes.STRICT,
    'allowed_packages': NetworkBlocker.AllowablePackages.DATASTORE,
}
