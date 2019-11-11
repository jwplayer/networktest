import socket
from pytest import fail

from networktest import (
    NetworkBlockException,
    NetworkBlockedTest,
    NetworkLimitedTest
)


def send():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(b'test', ('127.0.0.1', 80))


class TestBlockedCase(NetworkBlockedTest):

    def test_case(self):
        try:
            send()
            fail('Should fail')
        except NetworkBlockException:
            pass


class TestLimitedCase(NetworkLimitedTest):

    def test_case(self):
        try:
            send()
            fail('Should fail')
        except NetworkBlockException:
            pass
