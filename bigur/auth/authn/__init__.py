__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Business group for development management'
__licence__ = 'For license information see LICENSE'

from logging import getLogger

from aiohttp.web import Request

from .user_pass import UserPass

logger = getLogger(__name__)

authenticators = {'user_pass': UserPass()}


async def authenticate_end_user(http_request: Request) -> Request:
    logger.debug('Authentication of end user')

    http_request['user'] = await authenticators['user_pass'].authenticate(
        http_request)

    return http_request
