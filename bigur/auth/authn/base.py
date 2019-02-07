__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Business group for development management'
__licence__ = 'For license information see LICENSE'

from base64 import urlsafe_b64decode, urlsafe_b64encode
from os import urandom
from typing import Optional

from logging import getLogger

from aiohttp.web import Request, Response, View
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers.algorithms import AES
from cryptography.hazmat.primitives.ciphers.modes import CBC
from cryptography.hazmat.primitives.ciphers import Cipher

from bigur.utils import config

from bigur.auth.oauth2.rfc6749.errors import UserNotAuthenticated

logger = getLogger(__name__)

BLOCK_SIZE = 16


class AuthN(View):

    def set_cookie(self, response: Response, username: str):
        backend = default_backend()
        iv: bytes = urandom(BLOCK_SIZE)
        cipher = Cipher(
            AES(self.request.app['cookie_key']), CBC(iv), backend=backend)
        encryptor = cipher.encryptor()

        msg = username.encode('utf-8')
        padder = padding.PKCS7(BLOCK_SIZE * 8).padder()
        padded = (padder.update(msg) + padder.finalize())
        data = encryptor.update(padded) + encryptor.finalize()
        value = urlsafe_b64encode(iv + b':' + data).decode('utf-8')

        cookie_name: str = config.get(
            'user_pass', 'cookie_name', fallback='oidc')
        cookie_lifetime: int = config.getint(
            'user_pass', 'cookie_lifetime', fallback=3600)
        if config.getboolean('user_pass', 'cookie_secure', fallback=True):
            cookie_secure: Optional[str] = 'yes'
        else:
            cookie_secure = None

        response.set_cookie(
            cookie_name,
            value,
            max_age=cookie_lifetime,
            secure=cookie_secure,
            httponly='yes')


async def authenticate_end_user(http_request: Request) -> Request:
    logger.debug('Authentication of end user')

    # First check existing cookie, if it valid - pass
    cookie_name: str = config.get('user_pass', 'cookie_name', fallback='oidc')
    value = http_request.cookies.get(cookie_name)

    # Check cookie
    if value:
        logger.debug('Found cookie %s', value)

        # Initialize crypt backend
        backend = default_backend()

        iv, data = urlsafe_b64decode(value).split(b':', maxsplit=1)

        cipher = Cipher(
            AES(http_request.app['cookie_key']), CBC(iv), backend=backend)
        decryptor = cipher.decryptor()
        padded = decryptor.update(data) + decryptor.finalize()
        unpadder = padding.PKCS7(BLOCK_SIZE * 8).unpadder()
        username = unpadder.update(padded) + unpadder.finalize()

        # XXX: Check cookie is not expired
        # XXX: Remove cookie if expired

    # If no valid cookie, try to authenticate via username/password
    # parameters.
    if value is None:
        logger.debug('Cookie is not set, redirecting to login form')
        if http_request.method == 'GET':
            params = http_request.query.copy()
        elif http_request.method == 'POST':
            params = (await http_request.post()).copy()
        else:
            raise ValueError('Unsupported http method: %s', http_request.method)
        params['next'] = http_request.path
        redirect_uri = config.get(
            'user_pass', 'login_endpoint', fallback='/auth/login')
        raise UserNotAuthenticated(
            'Authentication required',
            http_request,
            redirect_uri=redirect_uri,
            params=params)

    http_request['oauth2_request'].user = username

    return http_request
