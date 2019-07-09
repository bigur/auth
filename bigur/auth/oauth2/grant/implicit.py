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
    token: str
    state: Optional[str] = None


@dataclass
class OAuth2RSAJWT(RSAJWT):
    sub: str
    scope: List[str]


async def implicit_grant(request: OAuth2Request) -> OAuth2Response:
    assert request.owner is not None, (
        'Resource owner is not set, do auth first!')

    token = OAuth2RSAJWT(sub=request.owner, scope=list(request.scope))

    return OAuth2TokenResponse(
        token=token.encode(request.jwt_keys[0]), state=request.state)
