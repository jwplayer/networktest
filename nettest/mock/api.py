import re
import json
from unittest.mock import MagicMock
from copy import copy

from .http import HttpMock


class ApiMockEndpoint:
    """
        Describes mocking behavior for a single endpoint on an API managed by :class:`ApiMock`

        Attributes:
          operation_id (str): Used to identify the endpoint when accessing this object from :class:`ApiMockEndpoints`. This should be the operationId in the service's OpenAPI spec if it has one.
          match_pattern (str): Regular expression used to identify the endpoint.
          response (function, lambda): Function called to generate a response from a request to this endpoint.
          request_mock (MagicMock): Mock that contains information about when this endpoint was called and with what arguments.
    """

    def __init__(self, operation_id, match_pattern, response):
        self.operation_id = operation_id
        self.match_pattern = match_pattern
        self.response = response

        self.request_mock = MagicMock()
        # unimplemented but this could be a nice to have
        # self.response_mock = MagicMock()

    def __request_matches(self, data):
        return re.match(self.match_pattern, data)

    def __get_matched_response(self, data, mock):
        match = self.__request_matches(data)
        if match:
            groups = {key: value.decode() for key, value in match.groupdict().items()}
            (code, body) = self.response(groups)
            mock.code = code
            if body is not None:
                body = json.dumps(body).encode()
            mock.read = lambda: body

            self.request_mock(groups)

            return True

        return False

    def __copy__(self):
        return ApiMockEndpoint(
            self.operation_id,
            self.match_pattern,
            copy(self.response)
        )


class ApiMockEndpoints:
    """
        Returned by :class:`ApiMock`.__enter__ and used to expose a group of :class:`ApiMockEndpoint` that describes an API.
    """

    def __init__(self, endpoints):
        self.endpoints = {endpoint.operation_id: endpoint for endpoint in endpoints}

    def __getattr__(self, name):
        return self.endpoints[name]


class ApiMock(HttpMock):
    """
        Context manager that mocks HTTP requests for a list of known hostnames.
    """

    hostnames = ()
    endpoints = ()
    __mock_next_body = False

    def __init__(self, *args, **kwargs):
        self.endpoints = tuple(copy(endpoint) for endpoint in self.endpoints)
        super().__init__(*args, **kwargs)

    def __enter__(self):
        super().__enter__()
        return ApiMockEndpoints(self.endpoints)

    def __is_request_body(self, data):
        """
            True if the provided request data is for a request body.
            This is needed because the request body is sent separately from the rest of the request.
        """
        # I'm sure there's a much better way to determine this but
        #   I wanted to keep this simple and avoid reimplementing too much HTTP functionality
        return data[-4:] != b'\r\n\r\n'

    def __get_request_hostname(self, data):
        """
            Get a hostname from an HTTP request.
        """
        start = b'\r\nHost: '
        end = b'\r\n'

        if not self.__is_request_body(data) and start in data:
            hostname = data[data.find(start) + len(start):]
            hostname = hostname[:hostname.find(end)]
            if b':' in hostname:
                hostname = hostname[:hostname.find(b':')]
            hostname = hostname.decode()
            return hostname

    def __get_default_response(self):
        """
            The default response to return on all HTTP requests for the specified hostnames.
            By default this is a MagicMock.
        """
        mock = MagicMock()
        mock.getcode = lambda: mock.code
        return mock

    def __get_targeted_response(self, data):
        """
            A more specific response to return on all HTTP requests for the specified hostnames.

            Uses :class:`ApiMockEndpoint` to match regular expression for an endpoint to specific responses.
        """
        mock = self.__get_default_response()

        for endpoint in self.endpoints:
            if endpoint.__get_matched_response(data, mock):
                break

        return mock

    @staticmethod
    def mockable_send(self, data, mock):
        """
            A method that is called when an HTTP request is attempted.

            False is returned to cancel the actual HTTP request.

            Args:
                self(http.client.HTTPConnection): Reference to the HTTPConnection whose send method was called.
                data(bytes): bytes that will be sent in the HTTP request if not stopped.
                mock(context manager): A reference to the context manager that defines this mockable_send method.
        """
        hostname = mock.__get_request_hostname(data)
        if hostname and hostname in mock.hostnames:
            response_mock = mock.__get_targeted_response(data)
            if mock.mode == mock.Modes.MOCK:
                self.response_class = lambda *args, **kwargs: response_mock

            mock.__mock_next_body = True
            return False
        elif hostname:
            mock.__mock_next_body = False
        elif mock.__mock_next_body:
            mock.__mock_next_body = False
            return False
