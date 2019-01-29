__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Business group for development management'
__licence__ = 'For license information see LICENSE'

from base64 import urlsafe_b64encode
from logging import getLogger
from os import urandom
from typing import Dict, Optional
from urllib.parse import urlunparse, urlencode

from aiohttp_jinja2 import render_template
from aiohttp.web import Request, Response
from aiohttp.web_exceptions import (HTTPBadRequest)
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers.algorithms import AES
from cryptography.hazmat.primitives.ciphers.modes import CBC
from cryptography.hazmat.primitives.ciphers import Cipher
from cryptography.hazmat.primitives import padding

from bigur.utils import config
from bigur.auth.model import User
from bigur.auth.authn.user_pass import BLOCK_SIZE

logger = getLogger(__name__)

FIELD_LENGTH = 128


async def user_pass_handler(http_request: Request):
    if http_request.method == 'GET':
        context: Dict[str, str] = {}
        return render_template('login_form.j2', http_request, context)

    elif http_request.method == 'POST':
        post = (await http_request.post()).copy()

        if ('username' in post and 'password' in post):
            # Check incoming parameters
            username = str(post.pop('username')).strip()
            password = str(post.pop('password')).strip()

            # Check fields too long
            if (len(username) > FIELD_LENGTH or len(password) > FIELD_LENGTH):
                logger.warning(
                    'Recieve request with very long login/password field')
                raise HTTPBadRequest()

            # Finding user
            logger.debug('Try to find user %s in store', username)

            user = await User.find_one({'username': username})
            if user is None:
                logger.warning('User {} not found'.format(username))
            else:
                if user.verify_password(password):
                    # Login successful
                    logger.debug('Login for user %s successful', username)

                    # No next parameter, no way to redirect
                    if 'next' not in post:
                        response = Response(text='Login successful')

                    # Redirecting
                    else:
                        next_uri = post.pop('next')
                        url = http_request.url
                        response = Response(
                            status=303,
                            reason='See Other',
                            charset='utf-8',
                            headers={
                                'Location':
                                    urlunparse(
                                        (url.scheme, url.raw_host, next_uri, '',
                                         urlencode(post, doseq=True),
                                         url.raw_fragment))
                            })
                        response.set_status(303, 'See Other')

                    # Set cookie
                    backend = default_backend()
                    iv: bytes = urandom(BLOCK_SIZE)
                    cipher = Cipher(
                        AES(http_request.app['cookie_key']),
                        CBC(iv),
                        backend=backend)
                    encryptor = cipher.encryptor()

                    msg = user.username.encode('utf-8')
                    padder = padding.PKCS7(BLOCK_SIZE * 8).padder()
                    padded = (padder.update(msg) + padder.finalize())
                    data = encryptor.update(padded) + encryptor.finalize()
                    value = urlsafe_b64encode(iv + b':' + data).decode('utf-8')

                    cookie_name: str = config.get(
                        'user_pass', 'cookie_name', fallback='oidc')
                    cookie_lifetime: int = config.getint(
                        'user_pass', 'cookie_lifetime', fallback=3600)
                    if config.getboolean(
                            'user_pass', 'cookie_secure', fallback=True):
                        cookie_secure: Optional[str] = 'yes'
                    else:
                        cookie_secure = None

                    response.set_cookie(
                        cookie_name,
                        value,
                        max_age=cookie_lifetime,
                        secure=cookie_secure,
                        httponly='yes')

                    return response

                logger.warning(
                    'Password is incorrect for user {}'.format(username))

        # Show form
        context = {}
        return render_template('login_form.j2', http_request, context)

    else:
        raise ValueError('Unsupported method %s', http_request.method)
