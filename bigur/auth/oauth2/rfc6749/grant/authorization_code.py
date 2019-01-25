__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Business group for development management'
__licence__ = 'For license information see LICENSE'

from logging import getLogger

from aiohttp.web import Request, Response

from bigur.auth.oauth2.rfc6749.errors import UnsupportedResponseType


logger = getLogger(__name__)


async def authorization_code_grant(http_request: Request) -> Response:
    logger.warning('Authorization code grant stub')
    raise UnsupportedResponseType(
        'Authorization code grant is not implemented yet',
        http_request=http_request)
