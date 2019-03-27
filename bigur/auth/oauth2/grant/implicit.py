__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Business group for development management'
__licence__ = 'For license information see LICENSE'

from logging import getLogger

from aiohttp.web import Request

from bigur.auth.oauth2.exceptions import UnsupportedResponseType

logger = getLogger(__name__)


async def implicit_grant(request: Request) -> Request:
    assert request.get('user') is not None, (
        'User not set in request, do auth first!')

    logger.warning('Implicit grant stub')
    raise UnsupportedResponseType(
        'Implicit grant is not implemented yet', request=request)
    return request
