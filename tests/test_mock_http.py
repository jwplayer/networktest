import urllib.request
from unittest.mock import MagicMock
from pytest import fail

from networktest import NetworkBlocker, NetworkBlockException
from networktest.mock import HttpMock


def send_request():
    urllib.request.urlopen('http://127.0.0.1', timeout=0).read()


class TestMock(HttpMock):

    @staticmethod
    def mockable_send(self, data, mock):
        response_mock = MagicMock()
        response_mock.code = 200
        response_mock.getcode = lambda: response_mock.code
        self.response_class = lambda *args, **kwargs: response_mock
        return False


def test_request_mode_mock():
    with TestMock(mode=TestMock.Modes.MOCK) as send_mock:
        with NetworkBlocker():
            send_request()
        send_mock.assert_called_once()
        assert send_mock.call_args[0][1].startswith(b'GET /')


def test_request_mode_watch():
    with TestMock(mode=TestMock.Modes.WATCH) as send_mock:
        try:
            with NetworkBlocker():
                send_request()
            fail('Request should not be prevented by HttpMock')
        except NetworkBlockException:
            pass
        send_mock.assert_called_once()
        assert send_mock.call_args[0][1].startswith(b'GET /')


def test_request_mode_disabled():
    with TestMock(mode=TestMock.Modes.DISABLED) as send_mock:
        try:
            with NetworkBlocker():
                send_request()
            fail('Request should not be prevented by HttpMock')
        except NetworkBlockException:
            pass
        send_mock.assert_not_called()


def test_request_ignore():
    with HttpMock(mode=TestMock.Modes.MOCK) as send_mock:
        try:
            with NetworkBlocker():
                send_request()
            fail('Request should not be prevented by HttpMock')
        except NetworkBlockException:
            pass
        send_mock.assert_not_called()
