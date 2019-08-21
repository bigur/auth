__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Business group for development management'
__licence__ = 'For license information see LICENSE'

from pytest import fixture, mark
from urllib.parse import urlparse, parse_qs

from bigur.auth.handler.oidc import AuthorizationHandler

# TODO: return state when error response
# TODO: test response mode: normal and error


@fixture
async def auth_endpoint(app, authn_userpass):
    app.router.add_route('*', '/auth/authorize', AuthorizationHandler)


class TestOIDCAuthorizationEndpoint:
    '''Tests for authorization endpoint'''

    @mark.asyncio
    async def test_client_id_required(self, auth_endpoint, cli, login):
        response = await cli.post(
            '/auth/authorize',
            data={
                'scope': 'openid',
                'response_type': 'id_token',
                'redirect_uri': 'https://localhost/',
            },
            allow_redirects=False)
        assert 400 == response.status
        assert 'text/plain' == response.content_type
        assert '400: Missing \'client_id\' parameter' == await response.text()

    @mark.asyncio
    async def test_redirect_uri_required(self, auth_endpoint, cli, login):
        response = await cli.post(
            '/auth/authorize',
            data={
                'client_id': 'someid',
                'response_type': 'id_token',
                'scope': 'openid',
            })
        assert 400 == response.status
        assert 'text/plain' == response.content_type
        assert ('400: Missing \'redirect_uri\' '
                'parameter') == await response.text()

    @mark.asyncio
    async def test_response_type_required(self, auth_endpoint, cli, login):
        response = await cli.post(
            '/auth/authorize',
            data={
                'client_id': 'someid',
                'scope': 'openid',
                'redirect_uri': 'https://localhost/feedback',
            },
            allow_redirects=False)
        assert 303 == response.status
        assert 'application/octet-stream' == response.content_type

        assert 'location' in response.headers
        parsed = urlparse(response.headers['Location'])
        assert parsed.fragment is not None
        query = parse_qs(parsed.fragment)

        assert '/feedback' == parsed.path

        assert ({
            'error': ['invalid_request'],
            'error_description': ['Missing \'response_type\' parameter']
        } == query)

    @mark.asyncio
    async def test_invalid_response_type(self, auth_endpoint, cli, login):
        response = await cli.post(
            '/auth/authorize',
            data={
                'client_id': 'someid',
                'scope': 'openid',
                'redirect_uri': 'https://localhost/feedback',
                'response_type': 'some_type'
            },
            allow_redirects=False)
        assert 303 == response.status
        assert 'application/octet-stream' == response.content_type

        assert 'location' in response.headers
        parsed = urlparse(response.headers['Location'])
        assert parsed.fragment is not None
        query = parse_qs(parsed.fragment)

        assert '/feedback' == parsed.path

        assert ({
            'error': ['invalid_request'],
            'error_description': ['Invalid \'response_type\' parameter']
        } == query)

    @mark.asyncio
    async def test_scope_required(self, auth_endpoint, user, cli, login):
        response = await cli.post(
            '/auth/authorize',
            data={
                'client_id': 'someid',
                'redirect_uri': 'https://localhost/feedback',
                'response_type': 'id_token',
            },
            allow_redirects=False)
        assert 'application/octet-stream' == response.content_type

        assert 'location' in response.headers
        parsed = urlparse(response.headers['Location'])
        assert parsed.fragment is not None
        query = parse_qs(parsed.fragment)

        assert '/feedback' == parsed.path

        assert ({
            'error': ['invalid_request'],
            'error_description': ['Missing \'scope\' parameter']
        } == query)

    @mark.asyncio
    async def test_get_id_token(self, auth_endpoint, user, client, cli, login,
                                decode_token):
        response = await cli.post(
            '/auth/authorize',
            data={
                'client_id': 'incorrect',
                'scope': 'openid',
                'response_type': 'id_token',
                'nonce': '123',
                'redirect_uri': 'https://localhost/feedback?a=1',
            },
            allow_redirects=False)

        assert 303 == response.status

        assert 'location' in response.headers
        parsed = urlparse(response.headers['Location'])

        assert '/feedback' == parsed.path
        assert ({'a': ['1']} == parse_qs(parsed.query))

        assert parsed.fragment is not None
        query = parse_qs(parsed.fragment)

        assert set(query.keys()) == {'id_token'}

        token = decode_token(query['id_token'][0], audience='incorrect')
        assert ({'iss', 'sub', 'exp', 'iat', 'nonce',
                 'aud'} == set(token.keys()))
        assert ('https://localhost:8889' == token['iss'])
        assert (user.id == token['sub'])
        assert ('123' == token['nonce'])

    @mark.asyncio
    async def test_get_id_token_token(self, auth_endpoint, user, client, cli,
                                      login, decode_token):
        response = await cli.post(
            '/auth/authorize',
            data={
                'client_id': 'incorrect',
                'scope': 'openid',
                'response_type': 'id_token token',
                'nonce': '123',
                'redirect_uri': 'https://localhost/feedback?a=1',
            },
            allow_redirects=False)

        assert 303 == response.status

        assert 'location' in response.headers
        parsed = urlparse(response.headers['Location'])

        assert '/feedback' == parsed.path
        assert ({'a': ['1']} == parse_qs(parsed.query))

        assert parsed.fragment is not None
        query = parse_qs(parsed.fragment)

        assert set(query.keys()) == {'id_token', 'access_token'}

        token = decode_token(query['id_token'][0], audience='incorrect')
        assert ({'iss', 'sub', 'exp', 'iat', 'nonce', 'aud',
                 'at_hash'} == set(token.keys()))
        assert ('https://localhost:8889' == token['iss'])
        assert (user.id == token['sub'])
        assert ('123' == token['nonce'])

        from base64 import urlsafe_b64encode
        from hashlib import sha256
        at_hash = urlsafe_b64encode(
            sha256(query['access_token'][0].encode('utf-8')).digest()
            [:16]).decode('utf-8').rstrip('=')
        assert at_hash == token['at_hash']
