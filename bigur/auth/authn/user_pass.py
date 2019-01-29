__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Business group for development management'
__licence__ = 'For license information see LICENSE'

from base64 import urlsafe_b64decode
from logging import getLogger

from aiohttp.web import Request
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers.algorithms import AES
from cryptography.hazmat.primitives.ciphers.modes import CBC
from cryptography.hazmat.primitives.ciphers import Cipher

from bigur.utils import config

from bigur.auth.authn.base import AuthN
from bigur.auth.model import User
from bigur.auth.oauth2.rfc6749.errors import UserNotAuthenticated

logger = getLogger(__name__)

BLOCK_SIZE = 16
FIELD_LENGHT = 128


class UserPass(AuthN):
    '''End-user login & password authentication'''

    async def authenticate(self, http_request: Request) -> User:

        # First check existing cookie, if it valid - pass
        cookie_name: str = config.get(
            'user_pass', 'cookie_name', fallback='oidc')
        cookie = http_request.cookies.get(cookie_name)

        # Check cookie
        if cookie:
            logger.debug('Found cookie %s', cookie.value)

            # Initialize crypt backend
            backend = default_backend()

            iv, data = urlsafe_b64decode(cookie.value).split(b':', maxsplit=1)

            cipher = Cipher(
                AES(http_request.app['cookie_key']), CBC(iv), backend=backend)
            decryptor = cipher.decryptor()
            padded = decryptor.update(data) + decryptor.finalize()
            unpadder = padding.PKCS7(BLOCK_SIZE * 8).unpadder()
            username = unpadder.update(padded) + unpadder.finalize()

            http_request['oauth2_request']['user'] = username

            # XXX: Check cookie is not expired
            # XXX: Remove cookie if expired

        # If no valid cookie, try to authenticate via username/password
        # parameters.
        if cookie is None:
            logger.debug('Cookie is not set, redirecting to login form')
            if http_request.method == 'GET':
                params = http_request.query.copy()
            elif http_request.method == 'POST':
                params = (await http_request.post()).copy()
            else:
                raise ValueError('Unsupported http method: %s',
                                 http_request.method)
            params['next'] = http_request.path
            redirect_uri = config.get(
                'user_pass', 'login_endpoint', fallback='/auth/login')
            raise UserNotAuthenticated(
                'Authentication required',
                http_request,
                redirect_uri=redirect_uri,
                params=params)

        return http_request
