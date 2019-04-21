__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Development management business group'
__licence__ = 'For license information see LICENSE'

from pytest import fixture, mark

from bigur.auth.handler.oauth2 import AuthorizationHandler


@fixture
async def auth_endpoint(app, authn_userpass):
    app.router.add_route('*', '/auth/authorize', AuthorizationHandler)


class TestAuthorizationEndpoint(object):

    @mark.asyncio
    async def test_no_client_id(self, auth_endpoint, cli, login):
        response = await cli.post(
            '/auth/authorize',
            data={
                'redirect_uri': '/response',
                'response_type': 'token',
            },
            allow_redirects=False)
        assert response.status == 400
        assert response.content_type == 'text/plain'
        assert await response.text() == ('400: Missing \'client_id\' parameter')

    @mark.asyncio
    async def test_missing_redirect_uri(self, auth_endpoint, cli, login, debug):
        response = await cli.post(
            '/auth/authorize',
            data={
                'client_id': '123',
                'response_type': 'token',
            },
            allow_redirects=False)
        assert response.status == 400
        assert response.content_type == 'text/plain'
        assert await response.text() == (
            '400: Missing \'redirect_uri\' parameter')
