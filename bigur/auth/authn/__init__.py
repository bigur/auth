__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Business group for development management'
__licence__ = 'For license information see LICENSE'

from base64 import urlsafe_b64decode
from logging import getLogger

from aiohttp.web import Request

from bigur.utils import config

from .base import decrypt
from .oidc import OpenIDConnect
from .user_pass import UserPass

authenticators = {
    'userpass': UserPass,
    'google': OpenIDConnect,  # XXX: stub
}

logger = getLogger(__name__)


async def authenticate_end_user(request: Request) -> Request:
    logger.debug('Authentication of end user')

    # First check existing cookie, if it valid - pass
    cookie_name: str = config.get('general', 'cookie_name', fallback='oidc')
    value = request.cookies.get(cookie_name)

    # Check cookie
    if value:
        logger.debug('Found cookie %s', value)

        key = request.app['cookie_key']
        userid: str = decrypt(key, urlsafe_b64decode(value))

        # XXX: Check user's session is active
        # XXX: Remove cookie if expired
        logger.warning('Check cookie expirity stub')

    # If no valid cookie, try to authenticate user
    if value is None:
        logger.debug('Cookie is not set, detecting authn method')

        handler = None
        for acr in request['oauth2_request'].acr_values:
            if acr.startswith('idp:'):
                handler = OpenIDConnect(request)

        if handler is None:
            handler = UserPass(request)

        await handler.redirect_unauthenticated()

    request['oauth2_request'].userid = userid

    return request
