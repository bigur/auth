__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Development management business group'
__licence__ = 'For license information see LICENSE'

from bigur.auth.oauth2.context import Context
from bigur.auth.oauth2.exceptions import InvalidRequest, UnsupportedGrantType


def validate_grant_type(context: Context) -> Context:
    grant_type = context.oauth2_request.grant_type
    if not grant_type:
        raise InvalidRequest('Parameter `grant_type\' required.')
    if grant_type not in {'authorization_code'}:
        raise UnsupportedGrantType(
            'Grant type `{}\' is not supported.'.format(grant_type))
    return context
