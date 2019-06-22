__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Development management business group'
__licence__ = 'For license information see LICENSE'

from bigur.auth.handler.base import OAuth2Handler
from bigur.auth.oauth2.endpoint import AuthorizationEndpoint
from bigur.auth.oauth2.request import OAuth2Request


class AuthorizationHandler(OAuth2Handler):

    __endpoint__ = AuthorizationEndpoint
    __request_class__ = OAuth2Request
