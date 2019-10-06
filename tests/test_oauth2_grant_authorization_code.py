__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Development management business group'
__licence__ = 'For license information see LICENSE'

from urllib.parse import parse_qs, urlparse

from pytest import fixture, mark

from bigur.auth.handler.oauth2 import AuthorizationHandler, TokenHandler

# pylint: disable=unused-argument,redefined-outer-name

# TODO: The authorization server MAY fully or partially ignore the scope
#       requested by the client


@fixture
async def handlers(app, authn_userpass):
    app.router.add_route('*', '/auth/authorize', AuthorizationHandler)
    app.router.add_route('*', '/auth/token', TokenHandler)


class TestAuthorizationCodeGrant(object):
    '''Test OAuth2 authorization code grant'''

    @mark.asyncio
    async def test_client_id_required(
            self,
            handlers,
            cli,
            user,
            login,
            redirect_uri,
    ):
        response = await cli.post(
            '/auth/authorize',
            data={
                'response_type': 'code',
                'state': 'smthng',
                'redirect_uri': redirect_uri,
            },
            allow_redirects=False)

        assert response.status == 401

    @mark.asyncio
    async def test_response_type_required(
            self,
            handlers,
            cli,
            user,
            login,
            client,
            redirect_uri,
    ):
        response = await cli.post(
            '/auth/authorize',
            data={
                'client_id': client.id,
                'client_secret': '123',
                'redirect_uri': redirect_uri,
            },
            allow_redirects=False)

        assert response.status == 303
        query = parse_qs(urlparse(response.headers['Location']).fragment)
        assert set(query) == {'error', 'error_description'}
        assert query['error'] == ['invalid_request']
        assert (query['error_description'] == [
            'Missing `response_type\' parameter.'
        ])

    @mark.asyncio
    async def test_redirect_uri_absent(
            self,
            handlers,
            cli,
            user,
            login,
            client,
    ):
        response = await cli.post(
            '/auth/authorize',
            data={
                'response_type': 'code',
                'client_id': client.id,
                'client_secret': '123',
            },
            allow_redirects=False)

        assert response.status == 400
        assert await response.text() == (
            '400: Missing `redirect_uri\' parameter.')

    @mark.asyncio
    async def test_redirect_uri_not_absolute(
            self,
            handlers,
            cli,
            user,
            login,
            client,
    ):
        response = await cli.post(
            '/auth/authorize',
            data={
                'redirect_uri': '/relative/uri',
                'response_type': 'code',
                'client_id': client.id,
                'client_secret': '123',
            },
            allow_redirects=False)

        assert response.status == 400
        assert await response.text() == (
            '400: Not absolute path in `redirect_uri\' parameter.')

    @mark.asyncio
    async def test_redirect_uri_not_registered(
            self,
            handlers,
            cli,
            user,
            login,
            client,
    ):
        response = await cli.post(
            '/auth/authorize',
            data={
                'redirect_uri': 'http://disney.com/contacts',
                'response_type': 'code',
                'client_id': client.id,
                'client_secret': '123',
            },
            allow_redirects=False)

        assert response.status == 400
        assert await response.text() == (
            '400: This `redirect_uri\' value is not allowed.')

    @mark.asyncio
    async def test_redirect_uri_w_query(self):
        raise NotImplementedError

    @mark.asyncio
    async def test_redirect_uri_w_fragment(self):
        raise NotImplementedError

    @mark.asyncio
    async def test_default_scopes(self):
        '''Scope not present in request, default scopes
        returned.'''
        raise NotImplementedError

    @mark.asyncio
    async def test_invalid_scope(self):
        '''Invalid scope required.'''
        raise NotImplementedError

    @mark.asyncio
    async def test_no_default_scopes(self):
        '''Scope not present in request, but no default
        scopes in system.'''
        raise NotImplementedError

    @mark.asyncio
    async def test_state(self):
        '''Copy state from request and return it.'''
        raise NotImplementedError

    @mark.asyncio
    async def test_return_code(self, handlers, cli, user, login, client):
        response = await cli.post(
            '/auth/authorize',
            data={
                'response_type': 'code',
                'client_id': client.id,
                'client_secret': '123',
                'state': 'smthng',
                'redirect_uri': '/response',
            },
            allow_redirects=False)

        assert response.status == 303

        parsed = urlparse(response.headers['Location'])

        assert parsed.scheme == ''
        assert parsed.netloc == ''
        assert parsed.path == '/response'
        assert parsed.query == ''
        assert parsed.fragment

        query = parse_qs(parsed.fragment)
        assert {'code', 'state'} == set(query)

        assert query['code']
        assert query['state'] == ['smthng']
