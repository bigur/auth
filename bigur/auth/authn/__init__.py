__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Business group for development management'
__licence__ = 'For license information see LICENSE'

from base64 import urlsafe_b64decode
from logging import getLogger

from aiohttp.web import Request

from .base import decrypt
from .oidc import OpenIDConnect
from .user_pass import UserPass

logger = getLogger(__name__)


async def authenticate_end_user(request: Request) -> Request:
    logger.debug('Authenticating of end user')

    # First check existing cookie, if it valid - pass
    cookie_name: str = request.app['config'].get('authn.cookie.id_name')
    value = request.cookies.get(cookie_name)

    # Check cookie
    if value:
        logger.debug('Found cookie %s', value)

        key = request.app['cookie_key']
        userid: str = decrypt(key, urlsafe_b64decode(value))

        # XXX: Check user's session is active
        # XXX: Remove cookie if expired
        logger.warning('Check cookie expirity stub')

        request['user'] = userid

    # If no valid cookie, try to authenticate user
    if value is None:
        logger.debug('Cookie is not set, detecting authn method')

        handler = None
        for acr in request['oauth2_request'].acr_values:
            if acr.startswith('idp:'):
                logger.debug('Using OpenID Connect authn method')
                handler = OpenIDConnect(request)

        if handler is None:
            logger.debug('Using login/password authn method')
            handler = UserPass(request)

        await handler.authenticate()

    request['oauth2_request'].userid = userid

    return request
