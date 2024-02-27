import urllib.request
import urllib.error
from pytest import fail
import requests

from networktest import NetworkBlocker, NetworkBlockException
from networktest.mock import HttpApiMock, HttpApiMockEndpoint, HttpApiMockResponse


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
        ),
        HttpApiMockEndpoint(
            operation_id='test_raw_str',
            match_pattern=b'^GET /test_raw_str/(?P<test_id>.*?)/',
            response=lambda groups: HttpApiMockResponse(f"HTTP/1.1 418 I'm a teapot\n\n{groups['test_id']}")
        ),
        HttpApiMockEndpoint(
            operation_id='test_raw_bytes',
            match_pattern=b'^GET /test_raw_bytes/(?P<test_id>.*?)/',
            response=lambda groups: HttpApiMockResponse(b"HTTP/1.1 418 I'm a teapot\n\ntest")
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
        assert response.reason == 'OK'
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


def test_request_matched_endpoint_requests():
    with TestMock() as mock_test:
        with NetworkBlocker():
            response = requests.get('http://127.0.0.1/test/abc/')
        assert response.status_code == 418
        assert response.content == b'{"id": "abc"}'

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
            assert response.read() == b''
        assert mock_test.test.request_mock.called_once()
        assert response.getcode() == 204
        assert response.reason == 'No Content'


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


def test_request_matched_endpoint_raw_str():
    with TestMock() as mock_test:
        try:
            with NetworkBlocker():
                urllib.request.urlopen(
                    'http://127.0.0.1/test_raw_str/abc/', timeout=0
                ).read()
            fail('Request should raise HTTPError')
        except urllib.error.HTTPError as e:
            assert e.code == 418
            assert e.read() == b'abc'


def test_request_matched_endpoint_raw_bytes():
    with TestMock() as mock_test:
        try:
            with NetworkBlocker():
                urllib.request.urlopen(
                    'http://127.0.0.1/test_raw_bytes/abc/', timeout=0
                ).read()
            fail('Request should raise HTTPError')
        except urllib.error.HTTPError as e:
            assert e.code == 418
            assert e.read() == b'test'
