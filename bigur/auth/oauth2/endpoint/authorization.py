__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Development management business group'
__licence__ = 'For license information see LICENSE'

from logging import getLogger

from rx import Observable, just
from rx import operators as op

from bigur.auth.oauth2.grant import (authorization_code_grant, implicit_grant)
from bigur.auth.oauth2.exceptions import InvalidRequest
from bigur.auth.oauth2.request import OAuth2Request
from bigur.auth.oauth2.response import OAuth2Response
from bigur.auth.oauth2.validators import (
    validate_client_id,
    authenticate_client,
    validate_redirect_uri,
    validate_response_type,
)

from bigur.auth.utils import call_async

logger = getLogger(__name__)


def select_flow(request: OAuth2Request) -> Observable:
    response_type = next(iter(request.response_type))

    if response_type == 'code':
        return just(request).pipe(
            op.flat_map(call_async(authorization_code_grant)))
    elif response_type == 'token':
        return just(request).pipe(op.flat_map(call_async(implicit_grant)))
    elif response_type == 'id_token':
        return just(request).pipe(op.flat_map(call_async(implicit_grant)))
    else:
        raise InvalidRequest('Invalid response_type parameter')


def get_authorization_stream(request: OAuth2Request) -> Observable:
    return just(request).pipe(
        op.flat_map(call_async(validate_client_id)),
        op.flat_map(call_async(authenticate_client)),
        op.flat_map(call_async(validate_redirect_uri)),
        op.flat_map(call_async(validate_response_type)),
        op.flat_map(select_flow))
