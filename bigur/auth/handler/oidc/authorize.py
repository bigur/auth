__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Development management business group'
__licence__ = 'For license information see LICENSE'

from bigur.auth.handler.base import OAuth2Handler
from bigur.auth.oidc.endpoint import AuthorizationEndpoint
from bigur.auth.oidc.request import OIDCRequest


class AuthorizationHandler(OAuth2Handler):

    __endpoint__ = AuthorizationEndpoint
    __request_class__ = OIDCRequest
