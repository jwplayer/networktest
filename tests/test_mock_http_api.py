import urllib.request
import urllib.error
from pytest import fail

from networktest import NetworkBlocker, NetworkBlockException
from networktest.mock import HttpApiMock, HttpApiMockEndpoint


class TestMock(HttpApiMock):

    hostnames = [
        '127.0.0.1'
    ]

    endpoints = [
        HttpApiMockEndpoint(
            operation_id='test',
            match_pattern=b'^GET /test/(?P<test_id>.*?)/',
            response=lambda groups: (418, {
                'id': groups['test_id'],
            })
        )
    ]


def test_request_unmatched():
    with TestMock():
        try:
            with NetworkBlocker():
                urllib.request.urlopen('http://localhost', timeout=0).read()
            fail('Request should not be prevented by HttpApiMock')
        except NetworkBlockException:
            pass


def test_request_matched_hostname_only():
    with TestMock() as mock_test:
        with NetworkBlocker():
            response = urllib.request.urlopen('http://127.0.0.1', timeout=0)
            response.read()
        assert response.getcode() == 200
        mock_test.test.request_mock.assert_not_called()


def test_request_matched_endpoint():
    with TestMock() as mock_test:
        try:
            with NetworkBlocker():
                urllib.request.urlopen(
                    'http://127.0.0.1/test/abc/', timeout=0
                ).read()
            fail('Request should raise HTTPError')
        except urllib.error.HTTPError as e:
            assert e.code == 418
            assert e.read() == b'{"id": "abc"}'
        mock_test.test.request_mock.assert_called_once()
        assert mock_test.test.request_mock.call_args[0][0] == {
            'test_id': 'abc'
        }


def test_request_override_response():
    with TestMock() as mock_test:
        mock_test.test.response = lambda groups: (204, None)
        with NetworkBlocker():
            response = urllib.request.urlopen(
                'http://127.0.0.1/test/abc/', timeout=0
            )
            assert response.read() is None
        assert mock_test.test.request_mock.called_once()
        assert response.getcode() == 204


def test_request_override_removed_nested_mock():
    with TestMock() as mock_test1:
        with TestMock() as mock_test2:
            mock_test2.test.response = lambda groups: (204, None)
            with NetworkBlocker():
                urllib.request.urlopen(
                    'http://127.0.0.1/test/abc/', timeout=0
                ).read()

        try:
            with NetworkBlocker():
                urllib.request.urlopen(
                    'http://127.0.0.1/test/abc/', timeout=0
                ).read()
            fail('Request should raise HTTPError')
        except urllib.error.HTTPError as e:
            assert e.code == 418
            assert e.read() == b'{"id": "abc"}'
        mock_test1.test.request_mock.assert_called_once()
        assert mock_test1.test.request_mock.call_args[0][0] == {
            'test_id': 'abc'
        }


def test_request_override_removed_mock_twice():
    with TestMock() as mock_test:
        mock_test.test.response = lambda groups: (204, None)
        with NetworkBlocker():
            urllib.request.urlopen(
                'http://127.0.0.1/test/abc/', timeout=0
            ).read()

    with TestMock() as mock_test:
        try:
            with NetworkBlocker():
                urllib.request.urlopen(
                    'http://127.0.0.1/test/abc/', timeout=0
                ).read()
            fail('Request should raise HTTPError')
        except urllib.error.HTTPError as e:
            assert e.code == 418
            assert e.read() == b'{"id": "abc"}'
        mock_test.test.request_mock.assert_called_once()
        assert mock_test.test.request_mock.call_args[0][0] == {
            'test_id': 'abc'
        }
