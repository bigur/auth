__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Business group for development management'
__licence__ = 'For license information see LICENSE'

from aiohttp.web import Request


class OAuth2Error(Exception):
    '''Base class for OAuth2 errors.'''

    def __init__(self, message: str, http_request: Request):
        self.http_request = http_request
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


class OAuth2RedirectError(OAuth2Error):
    '''This kind of exceptions should be return to user
    via redirection after `redirect_uri` check.'''

    error_code: str


class InvalidRequest(OAuth2RedirectError):
    error_code = 'invalid_request'


class UnsupportedResponseType(OAuth2RedirectError):
    error_code = 'unsupported_response_type'
