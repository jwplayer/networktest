import unittest

from .blocker import (
    NetworkBlocker,
    PRESET_KWARGS_BLOCKED,
    PRESET_KWARGS_LIMITED
)


class NetworkBlockerTest(unittest.TestCase):

    _blocker = None
    blocker_kwargs = {}

    def setUp(self):
        super().setUp()

        self._blocker = NetworkBlocker(**self.blocker_kwargs)
        self._blocker.__enter__()

    def tearDown(self):
        super().tearDown()

        self._blocker.__exit__(None, None, None)
        self._blocker = None


class NetworkBlockedTest(NetworkBlockerTest):
    """
        TestCase that prevents all network requests.

        Override or modify the blocker_kwargs attribute to configure
          the NetworkBlocker used.
    """

    blocker_kwargs = PRESET_KWARGS_BLOCKED


class NetworkLimitedTest(NetworkBlockerTest):
    """
        TestCase that prevents network requests except for those in a whitelist
          of packages commonly used for core functionality in an API
          (such as querying a database).

        Override or modify the blocker_kwargs attribute to configure
          the NetworkBlocker used.
    """

    blocker_kwargs = PRESET_KWARGS_LIMITED


__all__ = ('NetworkBlockedTest', 'NetworkLimitedTest')
