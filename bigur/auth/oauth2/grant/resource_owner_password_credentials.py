__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Business group for development management'
__licence__ = 'For license information see LICENSE'

from logging import getLogger

from aiohttp.web import Request, Response

from bigur.auth.oauth2.exceptions import UnsupportedResponseType

logger = getLogger(__name__)


async def resource_owner_password_credentials_grant(
        request: Request) -> Response:
    logger.warning('Resource owner password credentials grant stub')
    raise UnsupportedResponseType(
        'Resource owner password credentials grant is not implemented yet',
        request=request)
