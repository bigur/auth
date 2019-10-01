__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Development management business group'
__licence__ = 'For license information see LICENSE'

from dataclasses import asdict, dataclass
from logging import getLogger
from typing import Any, Dict, List

from rx import Observable, just, from_list
from rx import operators as op

from bigur.auth.oauth2.grant import (
    authorization_code_grant as oauth2_authorization_code_grant,
    implicit_grant as oauth2_implicit_grant,
)
from bigur.auth.oauth2.grant.implicit import OAuth2TokenResponse
from bigur.auth.oauth2.exceptions import InvalidRequest
from bigur.auth.oauth2.validators import (
    validate_client_id,
    authenticate_client,
    validate_redirect_uri,
)
from bigur.auth.oidc.grant import implicit_grant
from bigur.auth.oidc.grant.implicit import IDTokenResponse
from bigur.auth.oidc.request import OIDCRequest
from bigur.auth.oidc.validators import (
    validate_response_type,
    validate_scope,
)

from bigur.auth.utils import call_async

logger = getLogger(__name__)


@dataclass
class AuthorizationResponse(IDTokenResponse, OAuth2TokenResponse):
    pass


def select_flows(request: OIDCRequest) -> Observable:
    observables: List[Observable] = []
    for response_type in sorted(
            request.response_type, key=lambda x: x == 'id_token' and 1 or 0):
        if response_type == 'code':
            observables.append(
                just(request).pipe(
                    op.flat_map(call_async(oauth2_authorization_code_grant))))
        elif response_type == 'token':
            observables.append(
                just(request).pipe(
                    op.flat_map(call_async(oauth2_implicit_grant))))
        elif response_type == 'id_token':
            observables.append(
                just(request).pipe(op.flat_map(call_async(implicit_grant))))
        else:
            raise InvalidRequest('Invalid response_type parameter')
    return from_list(observables)


def get_authorization_stream(request: OIDCRequest) -> Observable:
    response_params: Dict[str, Any] = {}

    # yapf: disable
    return just(request).pipe(
        op.flat_map(call_async(validate_client_id)),
        op.flat_map(call_async(authenticate_client)),
        op.flat_map(call_async(validate_redirect_uri)),
        op.flat_map(call_async(validate_response_type)),
        op.flat_map(call_async(validate_scope)),
        op.flat_map(select_flows),
        op.merge_all(),
        op.do_action(lambda x: response_params.update(asdict(x))),
        op.last(),
        op.map(lambda x: AuthorizationResponse(**response_params)))
