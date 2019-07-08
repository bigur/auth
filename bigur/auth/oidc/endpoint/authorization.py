__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Development management business group'
__licence__ = 'For license information see LICENSE'

from logging import getLogger

from bigur.rx import ObservableType
from bigur.rx import operators as op

from bigur.auth.oauth2.endpoint.base import Endpoint
from bigur.auth.oauth2.exceptions import InvalidRequest, OAuth2Error
from bigur.auth.oauth2.validators import (
    validate_client_id, authenticate_client, validate_redirect_uri)
from bigur.auth.oidc.grant import (authorization_code_grant, implicit_grant)
from bigur.auth.oidc.request import OIDCRequest
from bigur.auth.oidc.validators import (validate_response_type)

logger = getLogger(__name__)


class AuthorizationEndpoint(Endpoint):

    def _chain(self, stream: ObservableType) -> ObservableType:

        base_branch = (
            stream
            | op.map(validate_client_id)
            | op.map(authenticate_client)
            | op.map(validate_redirect_uri)
            | op.map(validate_response_type))

        implicit_branch = (
            base_branch
            | op.filter(lambda x: x.response_type == {'token'})
            | op.map(implicit_grant))

        authorization_code_branch = (
            base_branch
            | op.filter(lambda x: x.response_type == {'code'})
            | op.map(authorization_code_grant))

        return base_branch
