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
class IDTokenResponse(OAuth2Response):
    id_token: bytes
    access_token: bytes

    @property
    def mode(self):
        return 'fragment'


async def implicit_grant(request: Request) -> Request:

    assert request.get('user') is not None, (
        'User not set in request, do auth first!')

    logger.warning('Implicit grant stub')

    # XXX: Token stub
    private_key = request.app['jwt_keys'][0]
    key = request.app['jwt_keys'][0].private_bytes(
        encoding=Encoding.PEM,
        format=PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=NoEncryption())
    from jwt import encode
    from time import time
    payload = {
        'iss': 'http://localhost:8889',
        'sub': request['user'].decode('utf-8'),
        'aud': request['oauth2_request'].client_id,
        'iat': time(),
        'exp': time() + 600
    }
    if request['oauth2_request'].nonce:
        payload['nonce'] = request['oauth2_request'].nonce

    public_key = private_key.public_key()
    numbers = public_key.public_numbers()
    n = numbers.n.to_bytes(int(public_key.key_size / 8), 'big').lstrip(b'\x00')
    from hashlib import sha1, sha256
    kid = sha1(n).hexdigest()

    from base64 import urlsafe_b64encode
    token = b'b1234'
    payload['at_hash'] = urlsafe_b64encode(
        sha256(token).digest()[:16]).decode('utf-8').rstrip('=')

    logger.debug('Payload: %s', payload)

    id_token = encode(payload, key, algorithm='RS256', headers={'kid': kid})

    request['oauth2_responses'].append(
        IDTokenResponse(id_token=id_token, access_token=token))

    return request
