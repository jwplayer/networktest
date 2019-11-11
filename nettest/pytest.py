class PytestIntegration:
    capman = None


try:
    import pytest
    # Removed in pytest 5.0
    if hasattr(pytest, 'config'):
        PytestIntegration.capman = \
            pytest.config.pluginmanager.getplugin('capturemanager')
except ImportError:
    pass


def pytest_configure(config):
    PytestIntegration.capman = config.pluginmanager.getplugin('capturemanager')
