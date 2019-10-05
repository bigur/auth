__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Development management business group'
__licence__ = 'For license information see LICENSE'

from typing import Type

from aiohttp.web import Response as HTTPResponse
from multidict import MultiDict
from rx import Observable

from bigur.auth.handler.base import OAuth2Handler
from bigur.auth.oauth2.context import Context
from bigur.auth.oauth2.endpoint import get_authorization_stream
from bigur.auth.oauth2.grant.authorization_code import (
    AuthorizationRequest,
    InvalidRequest,
)
from bigur.auth.oauth2.grant.implicit import TokenRequest


class AuthorizationHandler(OAuth2Handler):

    def get_request_class(self, params: MultiDict) -> Type:
        if 'response_type' in params:
            if params['response_type'] == 'code':
                return AuthorizationRequest
            if params['response_type'] == 'token':
                return TokenRequest
        return InvalidRequest

    def create_stream(self, context: Context) -> Observable:
        return get_authorization_stream(context)

    async def get(self) -> HTTPResponse:
        return await self.handle(self.request.query)

    async def post(self) -> HTTPResponse:
        return await self.handle(await self.request.post())
