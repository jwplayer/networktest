import socket
from pytest import fail, mark

from networktest import NetworkBlockException


def send():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(b'test', ('127.0.0.1', 80))


@mark.networkblocked
def test_strict_marker():
    try:
        send()
        fail('Should fail')
    except NetworkBlockException:
        pass


@mark.networklimited
def test_limited_marker():
    try:
        send()
        fail('Should fail')
    except NetworkBlockException:
        pass
