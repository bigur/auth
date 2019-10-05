__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Development management business group'
__licence__ = 'For license information see LICENSE'

from dataclasses import dataclass, field
from logging import getLogger
from typing import List, Optional, Set

from bigur.auth.oauth2.context import Context
from bigur.auth.oauth2.request import OAuth2Request
from bigur.auth.oauth2.response import OAuth2Response
from bigur.auth.oauth2.token import RSAJWT

logger = getLogger(__name__)


@dataclass
class TokenRequest(OAuth2Request):
    response_type: Set[str] = field(default_factory=set)
    client_id: Optional[str] = None
    redirect_uri: Optional[str] = None
    scope: Optional[str] = None
    state: Optional[str] = None


@dataclass
class OAuth2TokenResponse(OAuth2Response):
    access_token: Optional[str] = None
    state: Optional[str] = None


@dataclass
class OAuth2RSAJWT(RSAJWT):
    sub: str
    scope: List[str]


async def implicit_grant(context: Context) -> OAuth2Response:
    logger.debug('OAuth2 implicit grant')
    request = context.oauth2_request
    assert context.owner is not None, (
        'Resource owner is not set, do auth first!')

    request.access_token = OAuth2RSAJWT(
        sub=context.owner, scope=list(request.scope))

    return OAuth2TokenResponse(
        access_token=request.access_token.encode(context.jwt_keys[0]),
        state=request.state)
