import unittest

from . import NetworkBlocker


class NetworkBlockerTest(unittest.TestCase):

    _blocker = None
    _blocker_kwargs = {}

    def setUp(self):
        super().setUp()

        self._blocker = NetworkBlocker(**self._blocker_kwargs)
        self._blocker.__enter__()

    def tearDown(self):
        super().tearDown()

        self._blocker.__exit__(None, None, None)
        self._blocker = None


class NetworkBlockedTest(NetworkBlockerTest):
    """
        TestCase that prevents all network requests.
    """

    _blocker_kwargs = {
        'mode': NetworkBlocker.Modes.STRICT,
    }


class NetworkLimitedTest(NetworkBlockerTest):
    """
        TestCase that prevents network requests except for those in a whitelist
          of packages commonly used for core functionality in an API
          (such as querying a database).
    """

    _blocker_kwargs = {
        'mode': NetworkBlocker.Modes.STRICT,
        'allowed_packages': NetworkBlocker.AllowablePackages.DATASTORE,
    }


__all__ = ('NetworkBlockedTest', 'NetworkLimitedTest')
