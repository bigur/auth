__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Business group for development management'
__licence__ = 'For license information see LICENSE'

from logging import getLogger

from bigur.auth.oauth2.request import OAuth2Request

logger = getLogger(__name__)


async def validate_client_id(request: OAuth2Request) -> OAuth2Request:
    logger.warning('Validate client_id stub')
    return request
