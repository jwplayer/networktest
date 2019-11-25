import re
import json
from unittest.mock import MagicMock
from copy import copy
from http.client import HTTPResponse
import io

from .http import HttpMock


__all__ = (
    'HttpApiMockEndpoint', 'HttpApiMockEndpoints',
    'HttpApiMock',
)


def make_response_class(status_code, body):

    status = str(status_code)
    data = 'HTTP/1.1 {status}\n\n{body}'.format(
        status=status,
        body=body
    ).encode()

    class HttpApiMockResponse(HTTPResponse):
        def __init__(self, sock, *args, **kwargs):
            sock = MagicMock()
            super().__init__(sock, *args, **kwargs)

            self.fp = io.BytesIO(data)

    return HttpApiMockResponse


class HttpApiMockEndpoint:
    """
        Describes mocking behavior for a single endpoint on an API managed by
          :class:`HttpApiMock`

        Attributes:
          operation_id (str): Used to identify the endpoint when accessing
            this object from :class:`HttpApiMockEndpoints`. This should be the
            operationId in the service's OpenAPI spec if it has one.
          match_pattern (str): Regular expression used to identify
            the endpoint.
          response (function, lambda): Function called to generate
            a response from a request to this endpoint.
          request_mock (MagicMock): Mock that contains information about
            when this endpoint was called and with what arguments.
    """

    def __init__(self, operation_id, match_pattern, response):
        self.operation_id = operation_id
        self.match_pattern = match_pattern
        self.response = response

        self.request_mock = MagicMock()

    def __request_matches(self, data):
        return re.match(self.match_pattern, data)

    def _get_matched_response(self, data):
        match = self.__request_matches(data)
        if match:
            groups = {
                key: value.decode() for key, value in match.groupdict().items()
            }
            self.request_mock(groups)

            (code, body) = self.response(groups)
            if body is None:
                body = ''
            else:
                body = json.dumps(body)

            return make_response_class(
                status_code=code,
                body=body
            )

        return False

    def __copy__(self):
        return HttpApiMockEndpoint(
            self.operation_id,
            self.match_pattern,
            copy(self.response)
        )


class HttpApiMockEndpoints:
    """
        Returned by :class:`HttpApiMock`.__enter__ and used to expose
          a group of :class:`HttpApiMockEndpoint` that describes an API.
    """

    def __init__(self, endpoints):
        self.endpoints = {
            endpoint.operation_id: endpoint for endpoint in endpoints
        }

    def __getattr__(self, name):
        return self.endpoints[name]


class HttpApiMock(HttpMock):
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
        return HttpApiMockEndpoints(self.endpoints)

    def __is_request_body(self, data):
        """
            True if the provided request data is for a request body.
            This is needed because the request body is sent separately from
              the rest of the request.
        """
        # Is there a better way to confirm this without:
        #   * reimplementing HTTP library code
        #   * overcomplicating the solution
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
            The default response to return on all HTTP requests for the
              specified hostnames.
            By default this is a MagicMock.
        """
        return make_response_class(
            status_code=200,
            body=''
        )

    def __get_targeted_response(self, data):
        """
            A more specific response to return on all HTTP requests for
              the specified hostnames.

            Uses :class:`HttpApiMockEndpoint` to match regular expression for
              an endpoint to specific responses.
        """

        for endpoint in self.endpoints:
            response_class = endpoint._get_matched_response(data)
            if response_class:
                return response_class

        return self.__get_default_response()

    @staticmethod
    def mockable_send(self, data, mock):
        """
            A method that is called when an HTTP request is attempted.

            False is returned to cancel the actual HTTP request.

            Args:
                self(http.client.HTTPConnection): Reference to
                  the HTTPConnection whose send method was called.
                data(bytes): bytes that will be sent in the HTTP request if
                  not stopped.
                mock(context manager): A reference to the context manager that
                  defines this mockable_send method.
        """
        hostname = mock.__get_request_hostname(data)
        if hostname and hostname in mock.hostnames:
            response_class = mock.__get_targeted_response(data)
            if mock.mode == mock.Modes.MOCK:
                self.response_class = response_class

            mock.__mock_next_body = True
            return False
        elif hostname:
            mock.__mock_next_body = False
        elif mock.__mock_next_body:
            mock.__mock_next_body = False
            return False
