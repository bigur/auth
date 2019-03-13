__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Business group for development management'
__licence__ = 'For license information see LICENSE'

from pytest import mark
from urllib.parse import urlparse, parse_qs

from jwt import decode

# TODO: return state when error response
# TODO: test response mode: normal and error


class TestOIDCAuthorizationEndpoint(object):
    '''Tests for authorization endpoint'''

    @mark.db_configured
    @mark.asyncio
    async def test_scope_required(self, cli):
        response = await cli.post(
            '/auth/authorize',
            data={
                'client_id': 'someid',
                'response_type': 'token_id',
                'redirect_uri': 'https://localhost/',
            })
        assert response.status == 400
        assert response.content_type == 'text/plain'
        assert await response.text() == (
            '400: Missing 1 required argument: \'scope\'')

    @mark.db_configured
    @mark.asyncio
    async def test_client_id_required(self, cli):
        response = await cli.post(
            '/auth/authorize',
            data={
                'scope': 'openid',
                'response_type': 'token_id',
                'redirect_uri': 'https://localhost/',
            })
        assert response.status == 400
        assert response.content_type == 'text/plain'
        assert await response.text() == (
            '400: Missing 1 required argument: \'client_id\'')

    @mark.db_configured
    @mark.asyncio
    async def test_response_type_required(self, cli):
        response = await cli.post(
            '/auth/authorize',
            data={
                'client_id': 'someid',
                'scope': 'openid',
                'redirect_uri': 'https://localhost/',
            })
        assert response.status == 400
        assert response.content_type == 'text/plain'
        assert await response.text() == (
            '400: Missing 1 required argument: \'response_type\'')

    @mark.db_configured
    @mark.asyncio
    async def test_redirect_uri_required(self, cli):
        response = await cli.post(
            '/auth/authorize',
            data={
                'client_id': 'someid',
                'response_type': 'token_id',
                'scope': 'openid',
            })
        assert response.status == 400
        assert response.content_type == 'text/plain'
        assert await response.text() == (
            '400: Missing 1 required argument: \'redirect_uri\'')

    @mark.db_configured
    @mark.asyncio
    async def test_redirect_to_login_form(self, cli):
        response = await cli.post(
            '/auth/authorize',
            data={
                'client_id': 'first',
                'scope': 'openid',
                'response_type': 'token_id',
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
            'response_type': ['token_id'],
            'redirect_uri': ['https://localhost/feedback?a=1'],
            'next': ['/auth/authorize']
        }

    @mark.db_configured
    @mark.asyncio
    async def test_get_token_id(self, app, cli, login, debug):
        response = await cli.post(
            '/auth/authorize',
            data={
                'client_id': 'incorrect',
                'scope': 'openid',
                'response_type': 'token_id',
                'redirect_uri': 'https://localhost/feedback?a=1',
            },
            allow_redirects=False)

        assert response.status == 303

        location = urlparse(response.headers['Location'])

        assert location.path == '/feedback'

        assert parse_qs(location.query) == {'a': ['1']}

        aresp = parse_qs(location.fragment)
        assert set(aresp.keys()) == {'token_id'}
        jwt_key = app['jwt_keys'][0]
        from cryptography.hazmat.primitives.serialization import (Encoding,
                                                                  PublicFormat)
        b = jwt_key.public_key().public_bytes(
            encoding=Encoding.PEM, format=PublicFormat.SubjectPublicKeyInfo)
        token = decode(aresp['token_id'][0], b)
        assert token == {'sub': '123'}

    @mark.db_configured
    @mark.asyncio
    async def test_ignore_other_params(self, cli, debug):
        response = await cli.post(
            '/auth/authorize',
            data={
                'client_id': 'incorrect',
                'scope': 'openid',
                'response_type': 'token_id',
                'redirect_uri': 'https://localhost/feedback?a=1',
                'other': 'must_be_ignored'
            },
            allow_redirects=False)

        assert response.status == 200
        assert False, 'test is not ready'

    @mark.db_configured
    @mark.asyncio
    async def test_incorrect_client_id(self, cli, debug):
        response = await cli.post(
            '/auth/authorize',
            data={
                'scope': 'openid',
                'client_id': 'incorrect',
                'response_type': 'token_id',
                'redirect_uri': 'https://localhost/',
            },
            allow_redirects=False)

        assert response.status == 400
        assert response.content_type == 'text/plain; charset=utf-8'
        assert await response.text == 'Incorrect client_id.'
