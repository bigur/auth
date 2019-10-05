__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Development management business group'
__licence__ = 'For license information see LICENSE'

from typing import Type

from aiohttp.web import Response
from rx import Observable

from bigur.auth.handler.base import OAuth2Handler
from bigur.auth.oauth2.request import OAuth2Request
from bigur.auth.oauth2.context import Context


class TokenHandler(OAuth2Handler):

    def get_request_class(self) -> Type:
        return OAuth2Request

    def create_stream(self, context: Context) -> Observable:
        raise NotImplementedError('token enpoint not implemented yet')

    async def post(self) -> Response:
        return await self.handle(await self.request.post())
