__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Development management business group'
__licence__ = 'For license information see LICENSE'

from dataclasses import dataclass
from logging import getLogger
from typing import List, Optional

from bigur.auth.oauth2.request import OAuth2Request
from bigur.auth.oauth2.response import OAuth2Response
from bigur.auth.oauth2.token import RSAJWT

logger = getLogger(__name__)


@dataclass
class OAuth2TokenResponse(OAuth2Response):
    access_token: Optional[str] = None
    state: Optional[str] = None


@dataclass
class OAuth2RSAJWT(RSAJWT):
    sub: str
    scope: List[str]


async def implicit_grant(request: OAuth2Request) -> OAuth2Response:
    logger.debug('OAuth2 implicit grant')
    assert request.owner is not None, (
        'Resource owner is not set, do auth first!')

    request.access_token = OAuth2RSAJWT(
        sub=request.owner, scope=list(request.scope))

    return OAuth2TokenResponse(
        access_token=request.access_token.encode(request.jwt_keys[0]),
        state=request.state)
