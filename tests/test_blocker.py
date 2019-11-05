import socket
from pytest import fail

from nettest.blocker import NetworkBlocker, NetworkBlockException


def send():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(b'test', ('127.0.0.1', 80))


def test_mode_strict():
    with NetworkBlocker(mode=NetworkBlocker.Modes.STRICT):
        try:
            send()
            fail('Should fail')
        except NetworkBlockException:
            pass


def test_mode_warning(capsys):
    with NetworkBlocker(mode=NetworkBlocker.Modes.WARNING):
        send()
    err = capsys.readouterr().err
    assert len(err) > 0


def test_mode_disabled(capsys):
    with NetworkBlocker(mode=NetworkBlocker.Modes.DISABLED):
        send()
    err = capsys.readouterr().err
    assert len(err) == 0
