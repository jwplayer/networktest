nettest
=======

nettest makes it easier to test and enforce testing rules for Python applications that make network requests.

Installation
============

::

    pip install nettest

Blocking network requests
=========================

nettest provides a context manager NetworkBlocker that can be used to prevent tests or an application from making network requests.

::

    import urllib.request
    from nettest import NetworkBlocker

    with NetworkBlocker():
        # A NetworkBlockException will be raised
        urllib.request.urlopen('http://127.0.0.1').read()

In some types of tests you may want to allow certain types of requests but not others. When testing an API you may want to allow tests to access that API's database but not make requests to another API.

::

    import urllib.request
    from nettest import NetworkBlocker
    from my_database import Database

    with NetworkBlocker(allowed_packages=NetworkBlocker.AllowablePackages.FUNCTIONAL):
        # This is fine
        Database.query('SELECT 1')

        # A NetworkBlockException will be raised
        urllib.request.urlopen('http://127.0.0.1').read()

If you're in the process of migrating your tests to mock requests you may want to use NetworkBlocker's warning mode. This mode will allow requests but display a warning.

::

    import urllib.request
    from nettest import NetworkBlocker

    with NetworkBlocker(mode=NetworkBlocker.Modes.WARNING):
        # This will be allowed but a warning will be displayed
        urllib.request.urlopen('http://127.0.0.1').read()

Mocking API requests
====================

HttpApiMock is provided to help with mocking API requests in unit and functional tests.

::

    import urllib.request
    from nettest.mock import HttpApiMock

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
            # In most tests it would make sense to apply MyApiMock to all tests of a certain type and only explictly use MyApiMock when doing something like this.
            mock_api.example.response = lambda groups: (204, None)
            response = urllib.request.urlopen('http://my-api/')
            response.read()
            assert response.getcode() == 204

Integration tests
=================

HttpApiMock may also be used to create assertions for integration tests without preventing API requests from being made.

::

    import urllib.request
    from nettest.mock import HttpApiMock

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
        with MyApiMock(Mode=MyApiMock.Modes.WATCH) as mock_api:
            urllib.request.urlopen('http://my-api/example/1234/').read()
            mock_api.example.request_mock.assert_called_once()
