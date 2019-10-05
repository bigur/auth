__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Development management business group'
__licence__ = 'For license information see LICENSE'

from aiohttp.web import Response

from bigur.auth.handler.base import OAuth2Handler


class TokenHandler(OAuth2Handler):

    async def get(self) -> Response:
        return await self.handle(self.request.query)

    async def post(self) -> Response:
        return await self.handle(await self.request.post())
