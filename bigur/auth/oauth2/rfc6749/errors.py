__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Business group for development management'
__licence__ = 'For license information see LICENSE'

from typing import Dict, Optional
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

from aiohttp.web import Request


class OAuth2Error(Exception):
    '''Base class for OAuth2 errors.'''

    def __init__(self, message: str, request: Request):
        self.request = request
        super().__init__(message)


class OAuth2FatalError(OAuth2Error):
    '''This kind of exceptions should be returned via http response codes.'''


class InvalidClient(OAuth2FatalError):
    '''Raises then `client_id` verification failed'''


class InvalidClientCredentials(OAuth2FatalError):
    '''Raises then client authentication needed and it failed.'''


class InvalidRedirectURI(OAuth2FatalError):
    '''Raises then `redirect_uri` check failed.'''


class ParameterRequired(OAuth2FatalError):
    '''Raises then required parameter is absent.'''


class InvalidParameter(OAuth2FatalError):
    '''Raises then required parameter is invalid.'''


class OAuth2RedirectError(OAuth2Error):
    '''This kind of exceptions should be return to user
    via redirection after `redirect_uri` check.'''
    error_code: Optional[str]

    def __init__(self,
                 reason: str,
                 request: Request,
                 redirect_uri: Optional[str] = None,
                 params: Optional[Dict[str, str]] = None):
        self.redirect_uri = redirect_uri
        self.params = params
        super().__init__(reason, request)

    @property
    def location(self):
        request = self.request
        redirect_uri = self.redirect_uri
        if redirect_uri is None:
            redirect_uri = request['oauth2_request'].redirect_uri

        parts = urlparse(redirect_uri)

        query = parse_qs(parts.query)

        params = self.params

        if params is None:
            if self.error_code:
                params = {
                    'error': [self.error_code],
                    'error_description': [str(self)]
                }

            if 'oauth2_request' in request and (request['oauth2_request'].state
                                                is not None):
                params['state'] = [request['oauth2_request'].state]

        query.update(params)

        return urlunparse((parts.scheme, parts.netloc,
                           parts.path, parts.params,
                           urlencode(query, doseq=True), parts.fragment))


class UserNotAuthenticated(OAuth2RedirectError):
    error_code = None


class InvalidRequest(OAuth2RedirectError):
    error_code = 'invalid_request'


class UnsupportedResponseType(OAuth2RedirectError):
    error_code = 'unsupported_response_type'
