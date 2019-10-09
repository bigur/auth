__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Development management business group'
__licence__ = 'For license information see LICENSE'

from pytest import fixture, mark

from bigur.auth.handler.oauth2 import TokenHandler

# pylint: disable=unused-argument,redefined-outer-name


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
    async def test_client_id_required(
            self,
            token_endpoint,
            cli,
            user,
            login,
            client,
    ):
        response = await cli.post('/auth/token', data={}, allow_redirects=False)

        assert response.status == 401
        assert await response.json() == {
            'error': 'invalid_client',
            'error_description': 'Parameter `client_id\' is not set.',
        }

    @mark.asyncio
    async def test_no_client_password(
            self,
            token_endpoint,
            cli,
            user,
            login,
            client,
    ):
        response = await cli.post(
            '/auth/token',
            data={
                'client_id': client.id,
            },
            allow_redirects=False)

        assert response.status == 401
        assert await response.json() == {
            'error': 'invalid_client',
            'error_description': 'Client\'s credentials not specified.',
        }

    @mark.asyncio
    async def test_invalid_client_password(
            self,
            token_endpoint,
            cli,
            user,
            login,
            client,
    ):
        response = await cli.post(
            '/auth/token',
            data={
                'client_id': client.id,
                'client_secret': '1234',
            },
            allow_redirects=False)

        assert response.status == 401
        assert await response.json() == {
            'error': 'invalid_client',
            'error_description': 'Invalid client\'s password.',
        }

    @mark.asyncio
    async def test_miss_grant_type(
            self,
            token_endpoint,
            cli,
            user,
            login,
            client,
    ):
        response = await cli.post(
            '/auth/token',
            data={
                'client_id': client.id,
                'client_secret': '123',
            },
            allow_redirects=False)

        assert response.status == 400
        assert await response.json() == {
            'error': 'invalid_request',
            'error_description': 'Parameter `grant_type\' required.'
        }

    @mark.asyncio
    async def test_invalid_grant_type(
            self,
            token_endpoint,
            cli,
            user,
            login,
            client,
    ):
        response = await cli.post(
            '/auth/token',
            data={
                'client_id': client.id,
                'client_secret': '123',
                'grant_type': 'invalid',
            },
            allow_redirects=False)

        assert response.status == 400
        assert await response.json() == {
            'error': 'unsupported_grant_type',
            'error_description': 'Grant type `invalid\' is not supported.'
        }
