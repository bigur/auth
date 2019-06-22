__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Development management business group'
__licence__ = 'For license information see LICENSE'

from dataclasses import dataclass
from logging import getLogger

from bigur.auth.oauth2.request import OAuth2Request
from bigur.auth.oauth2.response import OAuth2Response

logger = getLogger(__name__)


@dataclass
class AuthorizationCodeResponse(OAuth2Response):
    pass


async def authorization_code_grant(request: OAuth2Request) -> OAuth2Response:
    logger.warning('Authorization code grant stub')
    return AuthorizationCodeResponse()
