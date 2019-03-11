__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Business group for development management'
__licence__ = 'For license information see LICENSE'

from dataclasses import dataclass
from logging import getLogger

from aiohttp.web import Request
from cryptography.hazmat.primitives.serialization import (
    Encoding, PrivateFormat, NoEncryption)

from bigur.auth.oauth2.rfc6749.errors import UnsupportedResponseType
from bigur.auth.oauth2.rfc6749.request import OAuth2Response

logger = getLogger(__name__)


@dataclass
class TokenIDResponse(OAuth2Response):
    token_id: str

    @property
    def mode(self):
        return 'fragment'


async def implicit_grant(request: Request) -> Request:

    assert request.get('user') is not None, (
        'User not set in request, do auth first!')

    logger.warning('Implicit grant stub')

    # XXX: Token stub
    token_id = {}
    key = request.app['jwt_keys'][0].private_bytes(
        encoding=Encoding.PEM,
        format=PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=NoEncryption())
    print(key)
    request['oauth2_responses'].append(TokenIDResponse(token_id=token_id))

    return request
