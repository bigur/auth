__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Business group for development management'
__licence__ = 'For license information see LICENSE'

from logging import getLogger

from aiohttp.web import Request


logger = getLogger(__name__)


class AuthN:
    pass


async def authenticate_resource_owner(http_request: Request):
    logger.warning('authenticate_resource_owner() stub')
    return http_request
