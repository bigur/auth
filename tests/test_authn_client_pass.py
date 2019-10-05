__author__ = 'Gennady Kovalev <gik@bigur.ru>'
__copyright__ = '(c) 2016-2019 Development management business group'
__licence__ = 'For license information see LICENSE'

from urllib.parse import parse_qs, urlparse

from pytest import fixture, mark

from bigur.auth.model import Client

# pylint: disable=unused-argument,redefined-outer-name


@fixture(scope='function')
async def public_client_w_pass(store, user):
    yield await store.clients.put(
        Client(
            client_type='public',
            user_id=user.id,
            password='123',
            title='Test web client',
            redirect_uris=['http://localhost/feedback']))


@fixture(scope='function')
async def public_client_wo_pass(store, user):
    yield await store.clients.put(
        Client(
            client_type='public',
            user_id=user.id,
            title='Test web client',
            redirect_uris=['http://localhost/feedback']))


class TestAutnNClientPass:
    '''Test client client_id/password authentication'''

    @mark.asyncio
    async def test_no_client_id(
            self,
            authn_userpass,
            stub_endpoint,
            cli,
            login,
    ):
        response = await cli.post(
            '/auth/stub',
            data={
                'redirect_uri': '/response',
            },
            allow_redirects=False)
        assert response.status == 401
        assert await response.text() == ('401: Parameter `client_id\' '
                                         'is not set.')

    @mark.asyncio
    async def test_conf_no_password(
            self,
            authn_userpass,
            stub_endpoint,
            cli,
            login,
            client,
    ):
        response = await cli.post(
            '/auth/stub',
            data={
                'redirect_uri': '/response',
                'client_id': client.id
            },
            allow_redirects=False)
        assert response.status == 401
        assert await response.text() == ('401: Client\'s credentials '
                                         'not specified.')

    @mark.asyncio
    async def test_conf_bad_password(
            self,
            authn_userpass,
            stub_endpoint,
            cli,
            login,
            client,
    ):
        response = await cli.post(
            '/auth/stub',
            data={
                'redirect_uri': '/response',
                'client_id': client.id,
                'client_secret': 'blah',
            },
            allow_redirects=False)
        assert response.status == 403
        assert await response.text() == '403: Invalid client\'s password.'

    @mark.asyncio
    async def test_conf_auth(
            self,
            authn_userpass,
            stub_endpoint,
            cli,
            login,
            client,
    ):
        response = await cli.post(
            '/auth/stub',
            data={
                'redirect_uri': '/response',
                'client_id': client.id,
                'client_secret': '123',
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
        assert set(query) == {'test'}
        assert query['test'] == ['passed']

    @mark.asyncio
    async def test_pub_w_p_no_pass(
            self,
            authn_userpass,
            stub_endpoint,
            cli,
            login,
            public_client_w_pass,
    ):
        response = await cli.post(
            '/auth/stub',
            data={
                'redirect_uri': '/response',
                'client_id': public_client_w_pass.id
            },
            allow_redirects=False)
        assert response.status == 401
        assert await response.text() == ('401: Client\'s credentials '
                                         'not specified.')

    @mark.asyncio
    async def test_pub_w_p_bad_pass(
            self,
            authn_userpass,
            stub_endpoint,
            cli,
            login,
            public_client_w_pass,
    ):
        response = await cli.post(
            '/auth/stub',
            data={
                'redirect_uri': '/response',
                'client_id': public_client_w_pass.id,
                'client_secret': 'bad',
            },
            allow_redirects=False)
        assert response.status == 403
        assert await response.text() == '403: Invalid client\'s password.'

    @mark.asyncio
    async def test_pub_w_p_auth(
            self,
            authn_userpass,
            stub_endpoint,
            cli,
            login,
            public_client_w_pass,
    ):
        response = await cli.post(
            '/auth/stub',
            data={
                'redirect_uri': '/response',
                'client_id': public_client_w_pass.id,
                'client_secret': '123',
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
        assert set(query) == {'test'}
        assert query['test'] == ['passed']

    @mark.asyncio
    async def test_pub_wo_p_bad_pass(
            self,
            authn_userpass,
            stub_endpoint,
            cli,
            login,
            public_client_w_pass,
    ):
        response = await cli.post(
            '/auth/stub',
            data={
                'redirect_uri': '/response',
                'client_id': public_client_w_pass.id,
                'client_secret': 'bad',
            },
            allow_redirects=False)
        assert response.status == 403
        assert await response.text() == '403: Invalid client\'s password.'

    @mark.asyncio
    async def test_pub_wo_auth(
            self,
            authn_userpass,
            stub_endpoint,
            cli,
            login,
            public_client_wo_pass,
    ):
        response = await cli.post(
            '/auth/stub',
            data={
                'redirect_uri': '/response',
                'client_id': public_client_wo_pass.id,
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
        assert set(query) == {'test'}
        assert query['test'] == ['passed']
