from .integration import PytestIntegration
from ..blocker import (
    NetworkBlocker,
    PRESET_KWARGS_BLOCKED,
    PRESET_KWARGS_LIMITED
)


def pytest_configure(config):
    PytestIntegration.capman = config.pluginmanager.getplugin('capturemanager')


def pytest_runtest_setup(item):
    marks = (mark.name for mark in item.iter_markers())
    marks = list(marks)

    kwargs = None
    if 'networkblocked' in marks:
        kwargs = PRESET_KWARGS_BLOCKED
    elif 'networklimited' in marks:
        kwargs = PRESET_KWARGS_LIMITED

    if kwargs:
        item._blocker = NetworkBlocker(**kwargs)
        item._blocker.__enter__()


def pytest_runtest_teardown(item):
    if hasattr(item, '_blocker'):
        item._blocker.__exit__(None, None, None)
        del item._blocker
