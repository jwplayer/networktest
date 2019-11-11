import http
from unittest.mock import MagicMock
from enum import Enum, auto


class HttpMockManager:
    """
        Handles mocking of HTTP requests by multiple mocks.
    """

    __mocks = []
    __original_send = None
    __overriden_mocks = {}

    class Modes(Enum):
        MOCK = auto()
        WATCH = auto()
        DISABLED = auto()

    @classmethod
    def __mock_id(cls, mock):
        return mock.__class__.__name__

    @classmethod
    def __register_mock(cls, mock):
        """
            Adds a mock to the list of mocks to call when a request attempt
              is made.
        """
        if mock not in cls.__mocks:
            try:
                mock_id = cls.__mock_id(mock)
                override_mock = next(
                    existing_mock for existing_mock in cls.__mocks
                    if cls.__mock_id(existing_mock) == mock_id
                )
                if mock_id not in cls.__overriden_mocks:
                    cls.__overriden_mocks[mock_id] = []
                cls.__overriden_mocks[mock_id].append(override_mock)
                cls.__mocks.remove(override_mock)
            except StopIteration:
                pass

            cls.__mocks.append(mock)

    @classmethod
    def __unregister_mock(cls, mock):
        """
            Removes a mock from the list of mocks to call when a request
            attempt is made.
        """
        mock_id = cls.__mock_id(mock)

        if mock in cls.__mocks:
            cls.__mocks.remove(mock)
            if mock_id in cls.__overriden_mocks:
                overriden_mock = cls.__overriden_mocks[mock_id].pop()
                if len(cls.__overriden_mocks[mock_id]) == 0:
                    del cls.__overriden_mocks[mock_id]
                cls.__mocks.append(overriden_mock)

        if mock_id in cls.__overriden_mocks and \
                mock in cls.__overriden_mocks[mock_id]:
            cls.__overriden_mocks[mock_id].remove(mock)

    @staticmethod
    def __replacement_send(self, data, http_mock):
        """
            Replacement for http.client.HTTPConnection.send that can mock
              a request or send the request depending on the behavior of
              the mocks registered with this class.
        """
        for mock in http_mock.__mocks:
            if mock.mockable_send(self, data, mock) is False:
                mock.send_mock(self, data)
                if mock.mode == http_mock.Modes.MOCK:
                    return
        http_mock.__original_send(self, data)

    @classmethod
    def enter(cls, mock):
        """
            Register a mock with this class and begin mocking requests if
              we haven't already.

            Duplicate mocks of the same class will override each other.
            The last to call enter will be the only mock active.
            As mocks are removed the most recently active mock of the
              same class will be reactivated.
        """
        if mock.mode == cls.Modes.DISABLED:
            return

        cls.__register_mock(mock)

        if not cls.__original_send:
            cls.__original_send = http.client.HTTPConnection.send

            def fill_mock_args(connection, data):
                return cls.__replacement_send(connection, data, cls)
            http.client.HTTPConnection.send = fill_mock_args

    @classmethod
    def exit(cls, mock):
        """
            Unregister a mock with this class and stop mocking requests if
              no other mocks are active.
        """
        cls.__unregister_mock(mock)

        if not cls.__mocks and cls.__original_send is not None:
            http.client.HTTPConnection.send = cls.__original_send
            cls.__original_send = None


class HttpMock:
    """
        Context manager that optionally mocks HTTP requests.
        This class does nothing useful on its own but is
          intended to be extended.
    """

    Modes = HttpMockManager.Modes

    def __init__(self, mode=None):
        if mode is None:
            mode = self.Modes.MOCK
        self.mode = mode
        self.send_mock = MagicMock()

    def __enter__(self):
        HttpMockManager.enter(self)
        return self.send_mock

    def __exit__(self, type, value, traceback):
        HttpMockManager.exit(self)

    @staticmethod
    def mockable_send(self, data, mock):
        """
            A method that is called when an HTTP request is attempted and
              can be used to mock requests based on the data they contain.

            Return False to cancel the actual HTTP request.
            The easiest way to mock the response is by replacing
              self.response_class. ApiMock has an example of this.

            Args:
                self(http.client.HTTPConnection): Reference to the
                  HTTPConnection whose send method was called.
                data(bytes): bytes that will be sent in the HTTP request
                  if not stopped.
                mock(context manager): A reference to the context manager
                  that defines this mockable_send method.
        """
        pass
