__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Development management business group'
__licence__ = 'For license information see LICENSE'

from bigur.auth.oauth2.request import OAuth2Request
from bigur.auth.oauth2.exceptions import InvalidRequest


async def validate_response_type(request: OAuth2Request) -> OAuth2Request:
    if not request.response_type:
        raise InvalidRequest('Missing response_type parameter')

    if request.response_type - {'code', 'token'}:
        raise InvalidRequest('Invalid response_type parameter')

    if len(request.response_type) > 1:
        raise InvalidRequest('Invalid response_type parameter')

    return request
