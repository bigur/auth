__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Business group for development management'
__licence__ = 'For license information see LICENSE'

from logging import getLogger

from aiohttp.web import Request

from bigur.auth.oauth2.rfc6749.errors import UnsupportedResponseType

logger = getLogger(__name__)


async def implicit_grant(http_request: Request) -> Request:
    assert http_request['oauth2_request'].user is not None, (
        'User not set in request, do auth first!')

    logger.warning('Implicit grant stub')
    raise UnsupportedResponseType(
        'Implicit grant is not implemented yet', http_request=http_request)
    return http_request
