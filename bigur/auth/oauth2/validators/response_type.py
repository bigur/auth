__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Development management business group'
__licence__ = 'For license information see LICENSE'

from bigur.auth.oauth2.context import Context
from bigur.auth.oauth2.exceptions import InvalidRequest


async def validate_response_type(context: Context) -> Context:
    response_type = context.oauth2_request.response_type
    if not response_type:
        raise InvalidRequest('Missing response_type parameter')

    if response_type - {'code', 'token'}:
        raise InvalidRequest('Invalid response_type parameter')

    if len(response_type) > 1:
        raise InvalidRequest('Invalid response_type parameter')

    return context
