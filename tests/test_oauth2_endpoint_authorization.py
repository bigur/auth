__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Development management business group'
__licence__ = 'For license information see LICENSE'

from urllib.parse import urlencode, urlparse, parse_qs

from pytest import fixture, mark

from bigur.auth.handler.oauth2 import AuthorizationHandler

# pylint: disable=unused-argument,redefined-outer-name


@fixture
async def auth_endpoint(app, authn_userpass):
    app.router.add_route('*', '/auth/authorize', AuthorizationHandler)


class TestAuthorizationEndpoint:

    @mark.asyncio
    async def test_fragment_in_query(
            self,
            auth_endpoint,
            cli,
            login,
            client,
            redirect_uri,
    ):
        response = await cli.get(
            '/auth/authorize?{}#response_type=code'.format(
                urlencode({
                    'client_id': client.id,
                    'client_secret': '123',
                    'redirect_uri': redirect_uri,
                })),
            allow_redirects=False)

        assert response.status == 303

        query = parse_qs(urlparse(response.headers['Location']).fragment)
        assert set(query) == {'error', 'error_description'}
        assert query['error'] == ['invalid_request']
        assert (query['error_description'] == [
            'Missing `response_type\' parameter.'
        ])

    @mark.asyncio
    async def test_get_post_request(
            self,
            auth_endpoint,
            cli,
            login,
            client,
            redirect_uri,
    ):
        response = await cli.post(
            '/auth/authorize?response_type=code',
            data={
                'client_id': client.id,
                'client_secret': '123',
                'redirect_uri': redirect_uri,
            },
            allow_redirects=False)

        assert response.status == 303

        query = parse_qs(urlparse(response.headers['Location']).fragment)
        assert set(query) == {'code'}
        assert query['code']

    @mark.asyncio
    async def test_miss_response_type(
            self,
            auth_endpoint,
            cli,
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
        assert response.content_type == 'application/octet-stream'

        parsed = urlparse(response.headers['Location'])

        assert parsed.scheme == 'http'
        assert parsed.netloc == 'localhost:{}'.format(cli.port)
        assert parsed.path == '/feedback'
        assert parsed.query == ''
        assert parsed.fragment

        query = parse_qs(parsed.fragment)
        assert set(query) == {'error', 'error_description'}

        assert query['error'] == ['invalid_request']
        assert (query['error_description'] == [
            'Missing `response_type\' parameter.'
        ])

    @mark.asyncio
    async def test_invalid_response_type(
            self,
            auth_endpoint,
            cli,
            login,
            client,
            redirect_uri,
    ):
        response = await cli.post(
            '/auth/authorize',
            data={
                'client_id': client.id,
                'client_secret': '123',
                'response_type': 'invalid',
                'redirect_uri': redirect_uri,
            },
            allow_redirects=False)

        assert response.status == 303
        assert response.content_type == 'application/octet-stream'

        parsed = urlparse(response.headers['Location'])

        assert parsed.scheme == 'http'
        assert parsed.netloc == 'localhost:{}'.format(cli.port)
        assert parsed.path == '/feedback'
        assert parsed.query == ''
        assert parsed.fragment

        query = parse_qs(parsed.fragment)
        assert set(query) == {'error', 'error_description'}

        assert query['error'] == ['invalid_request']
        assert (query['error_description'] == [
            'Invalid `response_type\' parameter.'
        ])
