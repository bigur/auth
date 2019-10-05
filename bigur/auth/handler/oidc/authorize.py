__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Development management business group'
__licence__ = 'For license information see LICENSE'

from aiohttp.web import Response
from bigur.auth.handler.base import OAuth2Handler
from bigur.auth.oidc.endpoint import get_authorization_stream
from bigur.auth.oidc.request import OIDCRequest


class AuthorizationHandler(OAuth2Handler):

    __get_stream__ = get_authorization_stream
    __request_class__ = OIDCRequest

    async def get(self) -> Response:
        return await self.handle(self.request.query)

    async def post(self) -> Response:
        return await self.handle(await self.request.post())
