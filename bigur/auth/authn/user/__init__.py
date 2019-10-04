__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Development management business group'
__licence__ = 'For license information see LICENSE'

from base64 import urlsafe_b64decode
from logging import getLogger

from aiohttp.web import Request

from .base import decrypt
from .oidc import OpenIDConnect
from .registration import Registration  # noqa
from .user_pass import UserPass
from .token import Token

logger = getLogger(__name__)


async def authenticate_end_user(request: Request) -> Request:
    '''Do user authentication. Returns nothing if it passed
    and raises exception if authentication not passed.'''
    logger.debug('Authenticating of end user')

    # First check existing cookie, if it valid - pass
    cookie_name: str = request.app['config'].get('authn.cookie.id_name')
    cookie_value = request.cookies.get(cookie_name)

    # Check cookie
    if cookie_value:
        logger.debug('Found cookie, decoding')

        key = request.app['cookie_key']
        user_id: str = decrypt(key, urlsafe_b64decode(cookie_value))

        # XXX: Check user's session is active
        # XXX: Remove cookie if expired
        logger.warning('Check cookie expirity stub')

    # If no valid cookie, try to authenticate user
    if cookie_value is None:
        logger.debug('Cookie is not set, detecting authn method')

        handler = None

        logger.debug('Request params: %s', request['params'])

        if 'Authorization' in request.headers:
            logger.debug('Using token authn method')
            handler = Token(request)

        elif 'acr_values' in request['params']:
            for acr in request['params']['acr_values'].split(' '):
                if acr.startswith('idp:'):
                    logger.debug('Using OpenID Connect authn method')
                    handler = OpenIDConnect(request)
                    break

        if handler is None:
            logger.debug('Using login/password authn method')
            handler = UserPass(request)

        user_id = await handler.authenticate()

    request['user'] = user_id

    return request
