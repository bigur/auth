__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Development management business group'
__licence__ = 'For license information see LICENSE'

from logging import getLogger

from rx import Observable, return_value
from rx import operators as op

from bigur.auth.oauth2.context import Context
from bigur.auth.oauth2.grant import authorization_code_grant, implicit_grant
from bigur.auth.oauth2.exceptions import InvalidRequest
from bigur.auth.oauth2.validators import (
    validate_redirect_uri,
    validate_response_type,
    validate_scope,
)

from bigur.auth.utils import call_async

logger = getLogger(__name__)


def select_flow(context: Context) -> Observable:
    response_type = next(iter(context.oauth2_request.response_type))
    if response_type == 'code':
        return return_value(context).pipe(
            op.flat_map(call_async(authorization_code_grant)))
    if response_type == 'token':
        return return_value(context).pipe(
            op.flat_map(call_async(implicit_grant)))
    raise InvalidRequest('Invalid response_type parameter')


def get_authorization_stream(context: Context) -> Observable:
    return return_value(context).pipe(
        op.flat_map(call_async(validate_redirect_uri)),
        op.flat_map(call_async(validate_response_type)),
        op.flat_map(call_async(validate_scope)),
        op.flat_map(select_flow),
    )
