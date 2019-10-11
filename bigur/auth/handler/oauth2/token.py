__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Development management business group'
__licence__ = 'For license information see LICENSE'

from typing import Type

from aiohttp.web import Response
from multidict import MultiDict
from rx import Observable

from bigur.auth.handler.base import OAuth2Handler
from bigur.auth.oauth2.context import Context
from bigur.auth.oauth2.grant.authorization_code import (
    AccessTokenRequest,
    InvalidAccessTokenRequest,
)
from bigur.auth.oauth2.endpoint.token import get_token_stream


class TokenHandler(OAuth2Handler):

    def get_request_class(self, params: MultiDict) -> Type:
        if 'grant_type' in params:
            if params['grant_type'] == 'authorization_code':
                return AccessTokenRequest
        return InvalidAccessTokenRequest

    def create_stream(self, context: Context) -> Observable:
        return get_token_stream(context)

    def get_response_mode(self, context: Context) -> str:
        return 'json'

    async def post(self) -> Response:
        return await self.handle(await self.request.post())
