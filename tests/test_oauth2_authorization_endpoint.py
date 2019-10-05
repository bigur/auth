__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Development management business group'
__licence__ = 'For license information see LICENSE'

from urllib.parse import urlparse, parse_qs

from pytest import fixture, mark

from bigur.auth.handler.oauth2 import AuthorizationHandler


@fixture
async def auth_endpoint(app, authn_userpass):
    app.router.add_route('*', '/auth/authorize', AuthorizationHandler)


class TestAuthorizationEndpoint:

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
    async def test_miss_redirect_uri(self, auth_endpoint, cli, login):
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

    @mark.asyncio
    async def test_miss_response_type(
            self,
            auth_endpoint,
            cli,
            login,
    ):
        response = await cli.post(
            '/auth/authorize',
            data={
                'client_id': '123',
                'redirect_uri': '/response',
            },
            allow_redirects=False)

        assert response.status == 303
        assert response.content_type == 'application/octet-stream'

        parsed = urlparse(response.headers['Location'])

        assert parsed.scheme == ''
        assert parsed.netloc == ''
        assert parsed.path == '/response'
        assert parsed.query == ''
        assert parsed.fragment

        query = parse_qs(parsed.fragment)
        assert set(query) == {'error', 'error_description'}

        assert query['error'] == ['invalid_request']
        assert (query['error_description'] == [
            'Missing response_type parameter'
        ])

    @mark.asyncio
    async def test_implicit_grant(self, auth_endpoint, user, decode_token, cli,
                                  login):
        response = await cli.post(
            '/auth/authorize',
            data={
                'response_type': 'token',
                'client_id': '123',
                'scope': 'one two',
                'redirect_uri': '/response',
                'state': 'blah',
            },
            allow_redirects=False)

        assert 303 == response.status
        assert 'application/octet-stream' == response.content_type

        parsed = urlparse(response.headers['Location'])

        assert '' == parsed.scheme
        assert '' == parsed.netloc
        assert '/response' == parsed.path
        assert '' == parsed.query
        assert parsed.fragment

        query = parse_qs(parsed.fragment)
        assert {'access_token', 'state'} == {x for x in query.keys()}

        assert ['blah'] == query['state']

        payload = decode_token(query['access_token'][0])
        assert {'sub', 'scope'} == set(payload.keys())
        assert user.id == payload['sub']
        assert {'one', 'two'} == set(payload['scope'])

    @mark.asyncio
    async def test_extra_parameters(self, auth_endpoint, user, decode_token,
                                    cli, login):
        response = await cli.post(
            '/auth/authorize',
            data={
                'response_type': 'token',
                'client_id': '123',
                'scope': 'one two',
                'redirect_uri': '/response',
                'state': 'blah',
                'some': 'extra',
                'parameters': 'here'
            },
            allow_redirects=False)

        assert 303 == response.status

        parsed = urlparse(response.headers['Location'])
        query = parse_qs(parsed.fragment)
        assert {'access_token', 'state'} == {x for x in query.keys()}

    @mark.asyncio
    async def test_auth_code_grant(self, auth_endpoint, user, cli, login):
        response = await cli.post(
            '/auth/authorize',
            data={
                'response_type': 'code',
                'client_id': 'someid',
                'state': 'smthng',
                'redirect_uri': '/response',
            },
            allow_redirects=False)

        assert 303 == response.status

        parsed = urlparse(response.headers['Location'])

        assert '' == parsed.scheme
        assert '' == parsed.netloc
        assert '/response' == parsed.path
        assert '' == parsed.query
        assert parsed.fragment

        query = parse_qs(parsed.fragment)
        assert {'code', 'state'} == {x for x in query.keys()}

        assert ['smthng'] == query['state']
