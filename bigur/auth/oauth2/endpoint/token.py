__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Development management business group'
__licence__ = 'For license information see LICENSE'

from rx import Observable
from rx import operators as op, return_value

from bigur.auth.utils import call_async
from bigur.auth.oauth2.context import Context
from bigur.auth.oauth2.grant.authorization_code import get_token_by_code
from bigur.auth.oauth2.validators import (
    validate_grant_type,)


def get_token_stream(context: Context) -> Observable:
    return return_value(context).pipe(
        op.map(validate_grant_type), op.flat_map(call_async(get_token_by_code)))
