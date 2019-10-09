__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Business group for development management'
__licence__ = 'For license information see LICENSE'


class HTTPRequestError(Exception):
    '''Base class for errors, that must response as 400 Bad Request.'''


class InvalidRedirectionURI(HTTPRequestError):
    '''Raises if redirect_uri provided in request not verified.'''


class OAuth2Error(Exception):
    '''Base class for OAuth2 errors.'''


class InvalidRequest(OAuth2Error):
    '''The request is missing a required parameter, includes an
    invalid parameter value, includes a parameter more than
    once, or is otherwise malformed.'''


class InvalidClient(OAuth2Error):
    '''Client authentication failed (e.g., unknown client, no
    client authentication included, or unsupported
    authentication method).  The authorization server MAY
    return an HTTP 401 (Unauthorized) status code to indicate
    which HTTP authentication schemes are supported.  If the
    client attempted to authenticate via the "Authorization"
    request header field, the authorization server MUST
    respond with an HTTP 401 (Unauthorized) status code and
    include the "WWW-Authenticate" response header field
    matching the authentication scheme used by the client.'''


class UnauthorizedClient(OAuth2Error):
    '''The client is not authorized to request an access token
    using this method.'''


class AccessDenied(OAuth2Error):
    '''The resource owner or authorization server denied the
    request.'''


class UnsupportedResponseType(OAuth2Error):
    '''The authorization server does not support obtaining an
    access token using this method.'''


class InvalidScope(OAuth2Error):
    '''The requested scope is invalid, unknown, or malformed.'''


class InvalidGrant(OAuth2Error):
    '''The provided authorization grant (e.g., authorization
    code, resource owner credentials) or refresh token is
    invalid, expired, revoked, does not match the redirection
    URI used in the authorization request, or was issued to
    another client.'''


class UnsupportedGrantType(OAuth2Error):
    '''The authorization grant type is not supported by the
    authorization server.'''


class ServerError(OAuth2Error):
    '''The authorization server encountered an unexpected
    condition that prevented it from fulfilling the request.
    (This error code is needed because a 500 Internal Server
    Error HTTP status code cannot be returned to the client
    via an HTTP redirect.)'''


class TemporaryUnavailable(OAuth2Error):
    '''The authorization server is currently unable to handle
    the request due to a temporary overloading or maintenance
    of the server.  (This error code is needed because a 503
    Service Unavailable HTTP status code cannot be returned
    to the client via an HTTP redirect.)'''
