__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Development management business group'
__licence__ = 'For license information see LICENSE'

from aiohttp.web import Response, View
from pytest import fixture, mark

from bigur.auth.authn import authenticate_end_user


class EchoHandler(View):

    async def get(self):
        self.request['params'] = self.request.query
        await authenticate_end_user(self.request)
        return Response(body='test passed')


@fixture
def routing(app):
    app.router.add_route('*', '/auth/test', EchoHandler)


class TestTokenAuthn:

    @mark.asyncio
    async def test_auth(self, app, routing, cli, token):
        token_bytes = token.encode(app['jwt_keys'][0]).decode('utf-8')
        response = await cli.get(
            '/auth/test',
            headers={'Authorization': 'Bearer {}'.format(token_bytes)},
            allow_redirects=False)
        assert 200 == response.status
        assert 'test passed' == (await response.text())
