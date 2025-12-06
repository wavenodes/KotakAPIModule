from __future__ import absolute_import

import logging
import re
from six.moves.urllib.parse import urlencode
from kotak_api_wn.exceptions import ApiException

# Try to use orjson for faster JSON serialization, fallback to standard json
try:
    import orjson
    def json_dumps(obj):
        return orjson.dumps(obj).decode('utf-8')
    def json_loads(s):
        return orjson.loads(s)
except ImportError:
    import json
    json_dumps = json.dumps
    json_loads = json.loads

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class RESTClientObject(object):
    """REST API Client with connection pooling and optimized performance.

    This class is a client to perform requests to a REST API with
    persistent connections for improved latency.

    Attributes:
        configuration (dict): configuration for the API client
        session (requests.Session): persistent session with connection pooling
    """

    # Class-level session pool for connection reuse
    _session_pool = {}

    def __init__(self, configuration):
        """
        Initialize the API client with a configuration dictionary and connection pooling.

        :param configuration: dictionary of configuration parameters
        """
        self.configuration = configuration
        
        # Create a persistent session with connection pooling
        self.session = requests.Session()
        
        # Configure connection pooling and retries
        retry_strategy = Retry(
            total=3,
            backoff_factor=0.1,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"]
        )
        adapter = HTTPAdapter(
            pool_connections=10,
            pool_maxsize=20,
            max_retries=retry_strategy
        )
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)
        
        # Pre-compile regex patterns for better performance
        self._json_pattern = re.compile(r'json', re.IGNORECASE)
        self._form_pattern = re.compile(r'x-www-form-urlencoded', re.IGNORECASE)

    def request(self, method, url, query_params=None, headers=None,
                body=None):
        """Perform a request to the REST API with connection reuse.

        This method performs a request to the REST API using persistent
        connections for improved latency.

        :param method: HTTP request method (e.g. GET, POST, PUT)
        :param url: URL for the API endpoint
        :param query_params: (optional) query parameters for the API endpoint
        :param headers: (optional) headers for the API request
        :param body: (optional) request body for the API request
        :return: response from the API
        :raises: ApiException in case of a request error
        """
        method = method.upper()
        assert method in ['GET', 'HEAD', 'DELETE', 'POST', 'PUT',
                          'PATCH', 'OPTIONS']

        headers = headers or {}

        if 'Content-Type' not in headers:
            headers['Content-Type'] = 'application/json'

        try:
            # Build URL with query params once
            if query_params:
                url = f"{url}?{urlencode(query_params)}"
            
            if method in ['POST', 'PUT', 'PATCH', 'DELETE']:
                if self._json_pattern.search(headers['Content-Type']):
                    request_body = json_dumps(body) if body is not None else None
                    response = self.session.post(url=url, headers=headers, data=request_body)
                elif self._form_pattern.search(headers['Content-Type']):
                    request_body = {"jData": json_dumps(body)} if body is not None else {}
                    response = self.session.post(url=url, headers=headers, data=request_body)
                else:
                    msg = """In-Valid Content-Type in the Header Parameters"""
                    raise ApiException(status=0, reason=msg)
            elif method == 'GET':
                response = self.session.get(url=url, headers=headers)
            else:
                msg = """Cannot call the API with the provided HTTP Method"""
                raise ApiException(status=0, reason=msg)
        except Exception as e:
            msg = "{0}\n{1}".format(type(e).__name__, str(e))
            raise ApiException(status=0, reason=msg)

        return response
    
    def close(self):
        """Close the session and release connections."""
        if self.session:
            self.session.close()


