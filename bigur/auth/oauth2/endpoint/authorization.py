__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Development management business group'
__licence__ = 'For license information see LICENSE'

from logging import getLogger

from bigur.rx import ObservableBase, operators as op

from bigur.auth.oauth2.grant import (authorization_code_grant, implicit_grant)
from bigur.auth.oauth2.endpoint import Endpoint
from bigur.auth.oauth2.exceptions import (OAuth2Error, InvalidRequest)
from bigur.auth.oauth2.request import OAuth2Request
from bigur.auth.oauth2.validators import (
    validate_client_id, authenticate_client, validate_redirect_uri)

logger = getLogger(__name__)


class AuthorizationEndpoint(Endpoint):

    def _chain(self, stream: ObservableBase) -> ObservableBase:

        def invalid_request(error_class: OAuth2Error, description: str):

            def raise_exception(request: OAuth2Request) -> OAuth2Request:
                raise error_class(description, request)

            return raise_exception

        base_branch = (
            stream
            | op.map(validate_client_id)
            | op.map(authenticate_client)
            | op.map(validate_redirect_uri))

        empty_response_type_branch = (
            base_branch
            | op.filter(lambda x: not x.response_type)
            | op.map(
                invalid_request(InvalidRequest,
                                'Missing response_type parameter')))

        implicit_branch = (
            base_branch
            | op.filter(lambda x: x.response_type == {'token'})
            | op.map(implicit_grant))

        authorization_code_branch = (
            base_branch
            | op.filter(lambda x: x.response_type == {'code'})
            | op.map(authorization_code_grant))

        invalid_response_type_branch = (
            base_branch
            | op.filter(lambda x: x.response_type - {'code', 'token'})
            | op.map(
                invalid_request(InvalidRequest,
                                'Invalid response_type parameter')))

        return op.concat(empty_response_type_branch, authorization_code_branch,
                         implicit_branch, invalid_response_type_branch)
