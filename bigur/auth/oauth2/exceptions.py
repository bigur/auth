__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Business group for development management'
__licence__ = 'For license information see LICENSE'

from typing import Optional

from bigur.auth.oauth2.request import OAuth2Request


class OAuth2Error(Exception):
    '''Base class for OAuth2 errors.'''

    def __init__(self, description: str, request: OAuth2Request):
        self._request = request
        super().__init__(description)


class OAuth2FatalError(OAuth2Error):
    '''This kind of exceptions should be returned via http response codes.'''


class MissingClientID(OAuth2FatalError):
    '''Raises then client_id required parameter is missing.'''


class InvalidClientID(OAuth2FatalError):
    '''Raises then client_id parameter present, but it invalid.'''


class InvalidRedirectionURI(OAuth2FatalError):
    '''Raises then `redirect_uri` check failed.'''


class OAuth2RedirectionError(OAuth2Error):
    '''This kind of exceptions should be return to user
    via redirection after `redirect_uri` check.'''
    error_code: Optional[str]


class InvalidRequest(OAuth2RedirectionError):
    '''The request is missing a required parameter, includes an
    invalid parameter value, includes a parameter more than
    once, or is otherwise malformed.'''

    error_code = 'invalid_request'


class UnauthorizedClient(OAuth2RedirectionError):
    '''The client is not authorized to request an authorization
    code using this method.'''

    error_code = 'unauthorized_client'


class AccessDenied(OAuth2RedirectionError):
    '''The resource owner or authorization server denied the
    request.'''

    error_code = 'access_denied'


class UnsupportedResponseType(OAuth2RedirectionError):
    '''The authorization server does not support obtaining an
    authorization code using this method.'''

    error_code = 'unsupported_response_type'


class InvalidScope(OAuth2RedirectionError):
    '''The requested scope is invalid, unknown, or malformed.'''

    error_code = 'invalid_scope'


class ServerError(OAuth2RedirectionError):
    '''The authorization server encountered an unexpected
    condition that prevented it from fulfilling the request.
    (This error code is needed because a 500 Internal Server
    Error HTTP status code cannot be returned to the client
    via an HTTP redirect.)'''

    error_code = 'server_error'


class TemporarilyUnavailable(OAuth2RedirectionError):
    '''The authorization server is currently unable to handle
    the request due to a temporary overloading or maintenance
    of the server.  (This error code is needed because a 503
    Service Unavailable HTTP status code cannot be returned
    to the client via an HTTP redirect.)'''

    error_code = 'temporarily_unavailable'
