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
    async def test_scope_required(self, auth_endpoint, user, cli, login, debug):
        response = await cli.post(
            '/auth/authorize',
            data={
                'client_id': 'someid',
                'response_type': 'id_token',
                'redirect_uri': 'https://localhost/',
            },
            allow_redirects=False)
        assert response.status == 400
        assert response.content_type == 'text/plain'
        assert await response.text() == (
            '400: Missing 1 required argument: \'scope\'')

    @mark.asyncio
    async def test_redirect_to_login_form(self, cli):
        response = await cli.post(
            '/auth/authorize',
            data={
                'client_id': 'first',
                'scope': 'openid',
                'response_type': 'id_token',
                'redirect_uri': 'https://localhost/feedback?a=1',
            },
            allow_redirects=False)

        assert response.status == 303

        parts = urlparse(response.headers['Location'])

        assert parts.path == '/auth/login'

        query = parse_qs(parts.query)
        assert query == {
            'client_id': ['first'],
            'scope': ['openid'],
            'response_type': ['id_token'],
            'redirect_uri': ['https://localhost/feedback?a=1'],
            'next': ['/auth/authorize']
        }

    @mark.asyncio
    async def test_get_id_token(self, app, cli, login, debug):
        response = await cli.post(
            '/auth/authorize',
            data={
                'client_id': 'incorrect',
                'scope': 'openid',
                'response_type': 'id_token',
                'redirect_uri': 'https://localhost/feedback?a=1',
            },
            allow_redirects=False)

        assert response.status == 303

        location = urlparse(response.headers['Location'])

        assert location.path == '/feedback'

        assert parse_qs(location.query) == {'a': ['1']}

        aresp = parse_qs(location.fragment)
        assert set(aresp.keys()) == {'id_token'}
        jwt_key = app['jwt_keys'][0]
        from cryptography.hazmat.primitives.serialization import (Encoding,
                                                                  PublicFormat)
        b = jwt_key.public_key().public_bytes(
            encoding=Encoding.PEM, format=PublicFormat.SubjectPublicKeyInfo)
        token = decode(aresp['id_token'][0], b)
        assert token == {'sub': '123'}

    @mark.asyncio
    async def test_ignore_other_params(self, cli, debug):
        response = await cli.post(
            '/auth/authorize',
            data={
                'client_id': 'incorrect',
                'scope': 'openid',
                'response_type': 'id_token',
                'redirect_uri': 'https://localhost/feedback?a=1',
                'other': 'must_be_ignored'
            },
            allow_redirects=False)

        assert response.status == 200
        assert False, 'test is not ready'

    @mark.asyncio
    async def test_incorrect_client_id(self, cli, debug):
        response = await cli.post(
            '/auth/authorize',
            data={
                'scope': 'openid',
                'client_id': 'incorrect',
                'response_type': 'id_token',
                'redirect_uri': 'https://localhost/',
            },
            allow_redirects=False)

        assert response.status == 400
        assert response.content_type == 'text/plain; charset=utf-8'
        assert await response.text == 'Incorrect client_id.'
