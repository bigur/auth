__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Development management business group'
__licence__ = 'For license information see LICENSE'

from base64 import urlsafe_b64encode
from dataclasses import asdict, dataclass
from hashlib import sha256
from logging import getLogger
from pprint import pformat
from time import time
from typing import Optional

from bigur.auth.oauth2.request import OAuth2Request
from bigur.auth.oauth2.response import OAuth2Response
from bigur.auth.oauth2.token import RSAJWT

logger = getLogger(__name__)


@dataclass
class IDTokenResponse(OAuth2Response):
    id_token: Optional[bytes] = None
    state: Optional[str] = None

    @property
    def mode(self):
        return 'fragment'


@dataclass
class IDToken(RSAJWT):
    iss: str
    sub: str
    aud: str
    iat: int
    exp: int
    nonce: str
    at_hash: Optional[str] = None


async def implicit_grant(request: OAuth2Request) -> IDTokenResponse:
    logger.debug('Implicit grant')
    assert request.owner is not None, (
        'Resource owner is not set, do auth first!')

    token = IDToken(
        iss=request.config.get('oidc.iss'),
        sub=request.owner,
        aud=str(request.client_id),
        nonce=request.nonce,
        iat=int(time()),
        exp=int(time()) + 600)

    if request.access_token is not None:
        encoded_token = request.access_token.encode(request.jwt_keys[0])
        token.at_hash = urlsafe_b64encode(
            sha256(encoded_token).digest()[:16]).decode('utf-8').rstrip('=')

    logger.debug('Token payload:\n%s', pformat(asdict(token)))

    return IDTokenResponse(
        id_token=token.encode(request.jwt_keys[0]), state=request.state)
