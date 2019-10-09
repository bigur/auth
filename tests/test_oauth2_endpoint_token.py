__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Development management business group'
__licence__ = 'For license information see LICENSE'

from pytest import fixture, mark

from bigur.auth.handler.oauth2 import TokenHandler

# pylint: disable=unused-argument,redefined-outer-name

# TODO: client must use POST request
# TODO: Parameters sent without a value MUST be treated
# TODO: Unauthorized client must return 401 and json response


@fixture
async def token_endpoint(app, authn_userpass):
    app.router.add_route('*', '/auth/token', TokenHandler)


class TestTokenEndpoint(object):

    @mark.asyncio
    async def test_get_request(self, token_endpoint, cli, user, login, client):
        response = await cli.get(
            '/auth/token',
            params={
                'client_id': client.id,
                'client_secret': '123',
                'grant_type': 'code',
                'code': 'blah',
            },
            allow_redirects=False)

        assert response.status == 405

    @mark.asyncio
    async def test_miss_grant_type(
            self,
            token_endpoint,
            cli,
            user,
            login,
            client,
            debug,
    ):
        response = await cli.post(
            '/auth/token',
            data={
                'client_id': client.id,
                'client_secret': '123',
                'grant_type': 'code',
                'code': 'blah',
            },
            allow_redirects=False)

        assert response.status == 400
        assert False

    @mark.asyncio
    async def test_invalid_grant_type(self, token_endpoint, cli, user, login):
        raise NotImplementedError

    @mark.asyncio
    async def test_post_request(self, token_endpoint, cli, user, login):
        raise NotImplementedError
