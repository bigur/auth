__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Business group for development management'
__licence__ = 'For license information see LICENSE'

from dataclasses import dataclass
from logging import getLogger

from bigur.auth.oauth2.request import OAuth2Request
from bigur.auth.oauth2.response import OAuth2Response

logger = getLogger(__name__)


@dataclass
class OAuth2TokenResponse(OAuth2Response):
    redirect_uri: str
    token: str


async def implicit_grant(request: OAuth2Request) -> OAuth2Response:
    assert request.owner is not None, (
        'Resource owner is not set, do auth first!')

    logger.warning('Implicit grant stub')

    return OAuth2TokenResponse(redirect_uri=request.redirect_uri, token='blah')
