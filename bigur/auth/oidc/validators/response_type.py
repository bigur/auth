__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Development management business group'
__licence__ = 'For license information see LICENSE'

from logging import getLogger

from bigur.auth.oauth2.exceptions import InvalidRequest
from bigur.auth.oidc.request import OIDCRequest

logger = getLogger(__name__)

# yapf: disable
ALLOWED_TYPES = (
    {'code'},
    {'token'},
    {'id_token'},
    {'code', 'token'},
    {'code', 'id_token'},
    {'id_token', 'token'},
    {'code', 'id_token', 'token'}
)


# yapf: enable
async def validate_response_type(request: OIDCRequest) -> OIDCRequest:
    logger.debug('Validating response_type')

    response_type = request.response_type

    if not request.response_type:
        raise InvalidRequest('Missing \'response_type\' parameter')

    if response_type not in ALLOWED_TYPES:
        raise InvalidRequest('Invalid \'response_type\' parameter')

    return request
