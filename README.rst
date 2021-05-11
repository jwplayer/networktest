Networktest
===========

A library to test and enforce testing rules for Python applications that make network requests.

Installation
============

.. code-block:: bash

    pip install networktest

Blocking network requests
=========================

networktest provides a context manager NetworkBlocker that can be used to prevent tests or an application from making network requests.

.. code-block:: python

    import urllib.request
    from networktest import NetworkBlocker

    with NetworkBlocker():
        # A NetworkBlockException will be raised
        urllib.request.urlopen('http://127.0.0.1').read()

In some types of tests you may want to allow certain types of requests but not others. When testing an API you may want to allow tests to access that API's database but not make requests to another API.

.. code-block:: python

    import urllib.request
    from networktest import NetworkBlocker
    from my_database import Database

    with NetworkBlocker(allowed_packages=NetworkBlocker.AllowablePackages.DATASTORE):
        # This is fine
        Database.query('SELECT 1')

        # A NetworkBlockException will be raised
        urllib.request.urlopen('http://127.0.0.1').read()

If you're in the process of migrating your tests to mock requests you may want to use NetworkBlocker's warning mode. This mode will allow requests but display a warning.

.. code-block:: python

    import urllib.request
    from networktest import NetworkBlocker

    with NetworkBlocker(mode=NetworkBlocker.Modes.WARNING):
        # This will be allowed but a warning will be displayed
        urllib.request.urlopen('http://127.0.0.1').read()

TestCase Support
----------------

Some TestCases are provided that will apply NetworkBlocker to all tests in that case with some default settings.

.. code-block:: python

    import urllib.request
    from my_database import Database
    from networktest import NetworkBlockedTest, NetworkLimitedTest

    class MyTest(NetworkBlockedTest):

        def test_blocker(self):
            # A NetworkBlockException will be raised
            urllib.request.urlopen('http://127.0.0.1').read()

    class MyOtherTest(NetworkLimitedTest):

        def test_blocker(self):
            # This is fine
            Database.query('SELECT 1')

            # A NetworkBlockException will be raised
            urllib.request.urlopen('http://127.0.0.1').read()

pytest Support
--------------

pytest markers networkblocked and networklimited are available to apply NetworkBlocker to tests. These may be applied to modules, classes, methods or any other way pytest markers are supported.

.. code-block:: python

    from pytest import mark

    @mark.networkblocked
    def test_blocked(self):
        # A NetworkBlockException will be raised
        urllib.request.urlopen('http://127.0.0.1').read()

    @mark.networklimited
    def test_limited(self):
        # This is fine
        Database.query('SELECT 1')

        # A NetworkBlockException will be raised
        urllib.request.urlopen('http://127.0.0.1').read()

NetworkBlocker may be applied to an entire directory by adding an autouse fixture to a conftest.py file in that directory.

.. code-block:: python

    @pytest.fixture(scope='module', autouse=True)
    def networkblocker():
        with NetworkBlocker():
            yield

Mocking API requests
====================

HttpApiMock is provided to help with mocking API requests in unit and functional tests.

.. code-block:: python

    import urllib.request
    from networktest.mock import HttpApiMock

    class MyApiMock(HttpApiMock):

        hostnames = [
           'my-api'
        ]

        endpoints = [
            HttpApiMockEndpoint(
                operation_id='example',
                match_pattern=b'^GET /example/(?P<example_id>.*?)/',
                response=lambda groups: (418, {
                    'id': groups['example_id'],
                })
            )
        ]

    def test_my_api():
        with MyApiMock() as mock_api:
            response = urllib.request.urlopen('http://my-api/')
            response.read()
            # Requests which do not have a matched endpoint return a 200 response code by default
            assert response.getcode() == 200

            try:
                # This request matches the 'example' endpoint defined in MyApiMock
                urllib.request.urlopen('http://my-api/example/1234/').read()
            except urllib.error.HTTPError as e:
                # The response is the one defined for the 'example' endpoint
                assert e.code == 418
                assert e.read() == b'{"id": "1234"}'

            # It's possible to change the default responses inside of a test
            # In most tests it would make sense to apply MyApiMock to all tests of a certain type
            #   and only explictly use MyApiMock when doing something like this.
            mock_api.example.response = lambda groups: (204, None)
            response = urllib.request.urlopen('http://my-api/')
            response.read()
            assert response.getcode() == 204

Integration tests
=================

HttpApiMock may also be used to create assertions for integration tests without preventing API requests from being made.

.. code-block:: python

    import urllib.request
    from networktest.mock import HttpApiMock

    class MyApiMock(HttpApiMock):

        hostnames = [
            'my-api'
        ]

        endpoints = [
            HttpApiMockEndpoint(
                operation_id='example',
                match_pattern=b'^GET /example/(?P<example_id>.*?)/',
                response=lambda groups: (204, None)
            )
        ]

    def test_my_api():
        with MyApiMock(mode=MyApiMock.Modes.WATCH) as mock_api:
            urllib.request.urlopen('http://my-api/example/1234/').read()
            mock_api.example.request_mock.assert_called_once()


Versioning
==========

This package strictly follows `semantic versioning <https://semver.org>`_.
