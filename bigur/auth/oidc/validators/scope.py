__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Development management business group'
__licence__ = 'For license information see LICENSE'

from logging import getLogger

from bigur.auth.oauth2.exceptions import InvalidRequest
from bigur.auth.oidc.request import OIDCRequest

logger = getLogger(__name__)


async def validate_scope(request: OIDCRequest):
    logger.warning('Scope validation stub')
    if not request.scope:
        raise InvalidRequest('Missing \'scope\' parameter')
    return request
