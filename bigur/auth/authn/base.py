__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Business group for development management'
__licence__ = 'For license information see LICENSE'

from base64 import urlsafe_b64encode
from os import urandom
from typing import Optional

from logging import getLogger

from aiohttp.web import Request, Response, View
from aiohttp_cors import CorsViewMixin, ResourceOptions
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers.algorithms import AES
from cryptography.hazmat.primitives.ciphers.modes import CBC
from cryptography.hazmat.primitives.ciphers import Cipher

logger = getLogger(__name__)

BLOCK_SIZE = 16


def decrypt(key: bytes, value: bytes) -> str:
    backend = default_backend()

    iv = value[:BLOCK_SIZE]
    data = value[BLOCK_SIZE:]

    cipher = Cipher(AES(key), CBC(iv), backend=backend)
    decryptor = cipher.decryptor()

    padded = decryptor.update(data) + decryptor.finalize()
    unpadder = padding.PKCS7(BLOCK_SIZE * 8).unpadder()

    return (unpadder.update(padded) + unpadder.finalize()).decode('utf-8')


def crypt(key: bytes, username: str) -> bytes:
    backend = default_backend()

    iv: bytes = urandom(BLOCK_SIZE)

    cipher = Cipher(AES(key), CBC(iv), backend=backend)
    encryptor = cipher.encryptor()

    padder = padding.PKCS7(BLOCK_SIZE * 8).padder()
    padded = (padder.update(username.encode('utf-8')) + padder.finalize())

    return iv + encryptor.update(padded) + encryptor.finalize()


class AuthN(View, CorsViewMixin):

    cors_config = {
        "*": ResourceOptions(
            allow_credentials=True,
            allow_headers='*',
        )
    }

    def set_cookie(self, request: Request, response: Response, userid: str):

        key = request.app['cookie_key']
        value = urlsafe_b64encode(crypt(key, userid)).decode('utf-8')

        config = request.app['config']
        cookie_name: str = config.get('authn.cookie.id_name')
        cookie_max_age: int = config.get('authn.cookie.max_age')
        if config.get('authn.cookie.secure'):
            cookie_secure: Optional[str] = 'yes'
        else:
            cookie_secure = None

        logger.debug('Set cookie %s=%s', cookie_name, value)
        response.set_cookie(
            cookie_name,
            value,
            max_age=cookie_max_age,
            secure=cookie_secure,
            httponly='yes')

    async def authenticate(self):
        raise NotImplementedError
