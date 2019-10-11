__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Development management business group'
__licence__ = 'For license information see LICENSE'

from datetime import datetime
from urllib.parse import parse_qs, urlparse

from pytest import fixture, mark

from bigur.auth.handler.oauth2 import AuthorizationHandler, TokenHandler

# pylint: disable=unused-argument,redefined-outer-name

# TODO: The authorization server MAY fully or partially ignore the scope
#       requested by the client
# TODO: Not return scopes if identical with request's
# TODO: redirect_uri in token request must be same:
#         REQUIRED, if the "redirect_uri" parameter was included in the
#         authorization request as described in Section 4.1.1, and their
#         values MUST be identical.
# TODO: Get token


@fixture
def handlers(app, authn_userpass):
    app.router.add_route('*', '/auth/authorize', AuthorizationHandler)
    app.router.add_route('*', '/auth/token', TokenHandler)


@fixture
async def expired_access_code(store):
    yield await store.access_codes.create(
        code='test', created=datetime(1970, 1, 1), used=False)


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
    async def test_redirect_uri_w_query(
            self,
            handlers,
            cli,
            user,
            login,
            client,
            redirect_uri,
            scopes,
    ):
        response = await cli.post(
            '/auth/authorize',
            data={
                'redirect_uri': redirect_uri + '?foo=bar&foo=baz',
                'response_type': 'code',
                'client_id': client.id,
                'client_secret': '123',
            },
            allow_redirects=False)

        assert response.status == 303
        query = parse_qs(urlparse(response.headers['Location']).query)
        fragment = parse_qs(urlparse(response.headers['Location']).fragment)
        assert set(query) == {'foo'}
        assert set(fragment) == {'code'}
        assert set(query['foo']) == {'bar', 'baz'}

    @mark.asyncio
    async def test_redirect_uri_w_fragment(
            self,
            handlers,
            cli,
            user,
            login,
            client,
            redirect_uri,
            scopes,
    ):
        response = await cli.post(
            '/auth/authorize',
            data={
                'redirect_uri': redirect_uri + '?foo=bar#baz=xyz',
                'response_type': 'code',
                'client_id': client.id,
                'client_secret': '123',
            },
            allow_redirects=False)

        assert response.status == 303
        query = parse_qs(urlparse(response.headers['Location']).query)
        fragment = parse_qs(urlparse(response.headers['Location']).fragment)
        assert set(query) == {'foo'}
        assert set(fragment) == {'code'}
        assert set(query['foo']) == {'bar'}

    @mark.asyncio
    async def test_invalid_scope(
            self,
            handlers,
            cli,
            user,
            login,
            client,
            redirect_uri,
    ):
        '''Invalid scope required.'''
        response = await cli.post(
            '/auth/authorize',
            data={
                'redirect_uri': redirect_uri,
                'response_type': 'code',
                'client_id': client.id,
                'client_secret': '123',
                'scope': 'foo',
            },
            allow_redirects=False)

        assert response.status == 303
        query = parse_qs(urlparse(response.headers['Location']).query)
        fragment = parse_qs(urlparse(response.headers['Location']).fragment)
        assert set(query) == set()
        assert set(fragment) == {'error', 'error_description'}
        assert fragment['error'] == ['invalid_scope']
        assert (fragment['error_description'] == ['Invalid scope `foo\'.'])

    @mark.asyncio
    async def test_no_default_scopes(
            self,
            handlers,
            cli,
            user,
            login,
            client,
            redirect_uri,
    ):
        '''Scope not present in request, but no default
        scopes in system.'''
        response = await cli.post(
            '/auth/authorize',
            data={
                'redirect_uri': redirect_uri,
                'response_type': 'code',
                'client_id': client.id,
                'client_secret': '123',
            },
            allow_redirects=False)

        assert response.status == 303
        query = parse_qs(urlparse(response.headers['Location']).query)
        fragment = parse_qs(urlparse(response.headers['Location']).fragment)
        assert set(query) == set()
        assert set(fragment) == {'error', 'error_description'}
        assert fragment['error'] == ['invalid_scope']
        assert (fragment['error_description'] == [
            'No scope in request and no default scopes configured.'
        ])

    @mark.asyncio
    async def test_default_scopes(
            self,
            handlers,
            cli,
            user,
            login,
            client,
            redirect_uri,
            scopes,
            store,
    ):
        '''Scope not present in request, default scopes
        returned.'''
        response = await cli.post(
            '/auth/authorize',
            data={
                'redirect_uri': redirect_uri,
                'response_type': 'code',
                'client_id': client.id,
                'client_secret': '123',
            },
            allow_redirects=False)

        assert response.status == 303
        query = parse_qs(urlparse(response.headers['Location']).query)
        fragment = parse_qs(urlparse(response.headers['Location']).fragment)
        assert set(query) == set()
        assert set(fragment) == {'code'}
        code = await store.access_codes.get_by_code(fragment['code'][0])
        assert code
        assert set(code.scopes) == {'email', 'profile'}

    @mark.asyncio
    async def test_state(
            self,
            handlers,
            cli,
            user,
            login,
            client,
            redirect_uri,
            scopes,
    ):
        response = await cli.post(
            '/auth/authorize',
            data={
                'redirect_uri': redirect_uri,
                'response_type': 'code',
                'client_id': client.id,
                'client_secret': '123',
                'state': 'please return it'
            },
            allow_redirects=False)

        assert response.status == 303
        query = parse_qs(urlparse(response.headers['Location']).query)
        fragment = parse_qs(urlparse(response.headers['Location']).fragment)
        assert set(query) == set()
        assert set(fragment) == {'code', 'state'}

    @mark.asyncio
    async def test_return_code(
            self,
            handlers,
            cli,
            user,
            login,
            client,
            redirect_uri,
            scopes,
            store,
    ):
        response = await cli.post(
            '/auth/authorize',
            data={
                'response_type': 'code',
                'client_id': client.id,
                'client_secret': '123',
                'state': 'smthng',
                'redirect_uri': redirect_uri,
            },
            allow_redirects=False)

        assert response.status == 303

        parsed = urlparse(response.headers['Location'])

        assert parsed.scheme == 'http'
        assert parsed.netloc == 'localhost:{}'.format(cli.port)
        assert parsed.path == '/feedback'

        query = parse_qs(parsed.query)
        assert set(query) == set()

        fragment = parse_qs(parsed.fragment)
        assert set(fragment) == {'code', 'state'}

        found = False
        # pylint: disable=protected-access
        for code in store.access_codes._db.values():
            if fragment['code'][0] == code.code:
                found = True
                break
        assert found

    @mark.asyncio
    async def test_no_code_provided(
            self,
            handlers,
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
                'grant_type': 'authorization_code',
            },
            allow_redirects=False)

        assert response.status == 400
        assert await response.json() == {
            'error': 'invalid_request',
            'error_description': 'Parameter `code\' required.'
        }

    @mark.asyncio
    async def test_invalid_code(
            self,
            handlers,
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
                'grant_type': 'authorization_code',
                'code': 'not-existing'
            },
            allow_redirects=False)

        assert response.status == 400
        assert await response.json() == {
            'error': 'invalid_grant',
            'error_description': 'Invalid code provided.'
        }

    @mark.asyncio
    async def test_expired_code(
            self,
            handlers,
            cli,
            user,
            login,
            client,
            expired_access_code,
    ):
        response = await cli.post(
            '/auth/token',
            data={
                'client_id': client.id,
                'client_secret': '123',
                'grant_type': 'authorization_code',
                'code': 'test'
            },
            allow_redirects=False)

        assert response.status == 400
        assert await response.json() == {
            'error': 'invalid_grant',
            'error_description': 'Code expired.'
        }
